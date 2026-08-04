"""Deterministic signal evaluation for Career Coach priority recommendations.

Each recommended skill (from ``skill_gap.priority``) is scored against real,
user-owned data using up to four independent signals:

(a) JD evidence     - the skill appears in the user's stored JD-match missing-skill tally.
(b) Resume analysis - the skill is flagged for addition by the user's resume analysis.
(c) Roadmap overlap - the skill is reinforced inside the AI report's own roadmap/missing lists.
(d) Interview focus - the skill matches the user's weakest interview practice category.

Signals that cannot be evaluated (no JD matches yet, no resume analysis, no
practice data) are excluded from BOTH the supported count and the total, so a
missing data source never produces a misleading "0 of N".  The output is
integer counts plus a plain-language reasons list - never an AI-generated
confidence score.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"


def confidence_label(supported: int, total: int) -> str:
    """Bucket a real supported/total signal count into an honest confidence label.

    Pure derivation of the already-computed integer counts — never an
    AI-generated confidence. Ratios >= 0.75 are "high", >= 0.4 are "medium",
    everything else (including zero/no evaluable signals) is "low".
    """
    if total <= 0 or supported <= 0:
        return CONFIDENCE_LOW
    ratio = float(supported) / float(total)
    if ratio >= 0.75:
        return CONFIDENCE_HIGH
    if ratio >= 0.4:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_LOW


def _normalize(value: str) -> str:
    """Lowercase/whitespace-normalize a skill or category name for matching."""
    return (value or "").strip().lower()


def _matches(skill: str, haystack: str) -> bool:
    """True when two names refer to the same thing (case-insensitive substring)."""
    a = _normalize(skill)
    b = _normalize(haystack)
    if not a or not b:
        return False
    return a in b or b in a


def _eval_jd_signal(db: Session, user_id: int, skill: str) -> tuple:
    """Return (evaluable, reason) for the stored JD-match evidence signal.

    Evaluable only once the user has at least the skill-gap minimum sample
    size of saved JD matches, mirroring the analytics service.
    """
    from app.career.services.analytics_service import get_skill_gap_summary

    summary = get_skill_gap_summary(db, user_id)
    if not summary.get("has_data"):
        return False, None

    for entry in summary.get("top_missing_skills", []):
        if _matches(skill, entry["name"]):
            return True, (
                f"Missing in {entry['count']} of "
                f"{summary['total_applications']} saved job matches"
            )
    return True, None


def _collect_resume_analysis_skills(db: Session, user_id: int) -> List[str]:
    """Collect skill names flagged by the user's resume analyses.

    Walks the ``skill_suggestions.recommended`` / ``gaps`` entries of the
    newest fresh analysis records.  The same helper key names are read whether
    they live at the top level or nested under ``deep_analysis.ai_analysis``.
    """
    from app.models.resume_analysis import ResumeAnalysis

    rows = (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.user_id == user_id,
            ResumeAnalysis.is_stale == 0,
        )
        .order_by(ResumeAnalysis.created_at.desc(), ResumeAnalysis.id.desc())
        .all()
    )

    skills: List[str] = []

    def _walk(node) -> None:
        if isinstance(node, dict):
            if "skill_suggestions" in node:
                inner = node["skill_suggestions"]
                for bucket in ("recommended", "gaps"):
                    for item in (inner.get(bucket) or []) if isinstance(inner, dict) else []:
                        if isinstance(item, str) and item.strip():
                            skills.append(item.strip())
                        elif isinstance(item, dict):
                            name = item.get("skill") or item.get("name")
                            if isinstance(name, str) and name.strip():
                                skills.append(name.strip())
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for value in node:
                _walk(value)

    for row in rows:
        try:
            _walk(row.analysis_json or {})
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not read resume analysis %s: %s", row.id, exc)

    return skills


def _eval_resume_analysis_signal(
    db: Session, user_id: int, skill: str
) -> tuple:
    """Return (evaluable, reason) for the resume-analysis signal."""
    flagged = _collect_resume_analysis_skills(db, user_id)
    if not flagged:
        return False, None

    if any(_matches(skill, name) for name in flagged):
        return True, "Flagged as a skill to add in your resume analysis"
    return True, None


def _collect_roadmap_skills(report: dict) -> List[str]:
    """Collect skill names the AI report itself reinforces (missing + topics)."""
    names: List[str] = []

    skill_gap = report.get("skill_gap") or {}
    if isinstance(skill_gap, dict):
        for item in skill_gap.get("missing_skills") or []:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
            elif isinstance(item, dict):
                name = item.get("name") or item.get("skill")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())

    for stage in report.get("roadmap") or []:
        if not isinstance(stage, dict):
            continue
        for topic in stage.get("topics") or []:
            if isinstance(topic, str) and topic.strip():
                names.append(topic.strip())

    return names


def _eval_roadmap_signal(report: dict, skill: str) -> tuple:
    """Return (evaluable, reason) for the roadmap-overlap signal.

    Always evaluable: it is derived from the report itself.  It only fires
    when the same skill is reinforced elsewhere in the AI output, so a
    priority item that appears nowhere else still keeps an honest baseline.
    """
    if any(_matches(skill, name) for name in _collect_roadmap_skills(report)):
        return True, "Reinforced in your learning roadmap"
    return True, None


def _eval_interview_signal(
    db: Session, user_id: int, skill: str
) -> tuple:
    """Return (evaluable, reason) for the weakest-interview-category signal.

    Uses the same floor as the AI context builder: at least two sessions and
    a category with at least two scored answers, so the "weakest" label is
    grounded rather than a single-answer fluke.
    """
    MIN_SESSIONS = 2
    MIN_SCORED_QUESTIONS = 2

    from app.interview_prep.service import InterviewPrepService

    try:
        progress = InterviewPrepService.get_progress(db, user_id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not compute interview progress: %s", exc)
        return False, None

    if progress.overview.total_sessions < MIN_SESSIONS:
        return False, None

    candidates = [
        cat
        for cat in progress.by_category
        if cat.average_score is not None
        and cat.question_count >= MIN_SCORED_QUESTIONS
    ]
    if not candidates:
        return False, None

    weakest = min(candidates, key=lambda c: c.average_score)
    if _matches(skill, weakest.category):
        return True, (
            f"Targets your weakest interview area "
            f"({weakest.category}, avg {round(float(weakest.average_score), 1)})"
        )
    return True, None


def _evaluate_signals(report: dict, db: Session, user_id: int, skill: str) -> dict:
    """Score one recommended skill against every evaluable signal."""
    db_signals = [
        _eval_jd_signal,
        _eval_resume_analysis_signal,
        _eval_interview_signal,
    ]

    supported = 0
    total = 0
    reasons: List[str] = []

    def _apply(evaluable, reason) -> None:
        nonlocal supported, total
        if not evaluable:
            return
        total += 1
        if reason is not None:
            supported += 1
            reasons.append(reason)

    for evaluator in db_signals:
        _apply(*evaluator(db, user_id, skill))

    _apply(*_eval_roadmap_signal(report, skill))

    return {
        "skill": skill,
        "supported_signals": supported,
        "total_possible_signals": total,
        "reasons": reasons,
        "confidence": confidence_label(supported, total),
    }


def enrich_priority_recommendations(
    report: dict,
    db: Session,
    user_id: int,
) -> List[dict]:
    """Enrich every ``skill_gap.priority`` entry with deterministic signal counts.

    Each entry becomes ``{skill, supported_signals, total_possible_signals,
    reasons}``.  When no db/user_id are available the original items are
    returned untouched so callers keep the plain-string behaviour.
    """
    skill_gap = report.get("skill_gap") or {}
    if not isinstance(skill_gap, dict):
        return []

    priority = skill_gap.get("priority") or []
    if not priority:
        return []

    if db is None or user_id is None:
        return [item for item in priority if isinstance(item, str) or isinstance(item, dict)]

    enriched = []
    for item in priority:
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = item.get("skill") or item.get("name") or ""
        else:
            continue

        if not str(name).strip():
            continue

        enriched.append(_evaluate_signals(report, db, user_id, str(name)))

    return enriched
