"""Job application workspace assembly.

Builds the three "above the tabs" blocks for an application's workspace:

* ``next_action`` — deterministic recommendation from ``next_action.py``
* ``insights``    — dismissible insight cards (JD match gaps, resume analysis
                    suggestions) derived from data that already exists
* ``dismissed``   — insight keys the user has dismissed for this application

Everything here is a pure derivation over stored rows; no AI is called and no
new data is invented.
"""

import json
from datetime import date, datetime, timezone

from app.job_tracker.next_action import recommend_next_action
from app.models.cover_letter import CoverLetter
from app.communication.models import CommunicationMessage
from app.interview_prep.models import InterviewSession
from app.models.insight_dismissal import InsightDismissal
from app.services.jd_match_result_service import get_latest_result
from app.services.analysis_persistence_service import get_latest_analysis

INSIGHT_JD_MATCH_GAPS = "jd_match_gaps"
INSIGHT_RESUME_SUGGESTIONS = "resume_suggestions"

# Maximum number of individual reasons shown on a card before they collapse
# into a "+N more" summary.
MAX_INSIGHT_REASONS = 6


def _days_since_applied(job) -> int | None:
    """Whole days since the application was submitted.

    Prefers ``applied_date``; falls back to ``created_at``. Returns ``None``
    when neither is known so the follow-up rule never fires on unknown dates.
    """
    if getattr(job, "applied_date", None):
        delta = (date.today() - job.applied_date).days
        return max(delta, 0)
    created = getattr(job, "created_at", None)
    if created:
        now = datetime.now(timezone.utc) if created.tzinfo else datetime.now(timezone.utc).replace(tzinfo=None)
        return max((now - created).days, 0)
    return None


def _count(db, model, column, value) -> int:
    return db.query(model).filter(column == value).count()


def recommend_next_action_for_job(db, job) -> dict | None:
    """Gather the application's real completion state and run the decision tree."""
    has_jd_match = get_latest_result(db, job.user_id, job.id) is not None
    state = {
        "status": getattr(job, "status", ""),
        "has_job_description": bool((job.job_description or "").strip()),
        "has_resume": bool(job.resume_id),
        "has_jd_match": has_jd_match,
        "has_cover_letter": _count(
            db, CoverLetter, CoverLetter.job_application_id, job.id
        ) > 0,
        "has_communication": _count(
            db, CommunicationMessage, CommunicationMessage.related_job_application_id, job.id
        ) > 0,
        "has_interview_activity": _count(
            db, InterviewSession, InterviewSession.related_job_application_id, job.id
        ) > 0,
        "days_since_applied": _days_since_applied(job),
    }
    return recommend_next_action(state)


def _skill_name(item) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "Unknown")
    return str(item)


def _missing_skill_names(match_result) -> list[str]:
    items = match_result.missing_skills
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            return []
    return [_skill_name(item) for item in (items or [])]


def _resume_suggestions(db, user_id, resume_id) -> list[str]:
    if not resume_id:
        return []
    record = get_latest_analysis(db, resume_id, user_id)
    if record is None:
        return []
    analysis = record.analysis_json
    if isinstance(analysis, str):
        try:
            analysis = json.loads(analysis)
        except Exception:
            analysis = {}
    if not isinstance(analysis, dict):
        return []
    suggestions = analysis.get("suggestions") or []
    return [str(s) for s in suggestions if str(s).strip()]


def _card(key: str, title: str, description: str, reasons: list[str]) -> dict:
    return {
        "key": key,
        "title": title,
        "description": description,
        "reasons": reasons[:MAX_INSIGHT_REASONS],
        "extra_count": max(0, len(reasons) - MAX_INSIGHT_REASONS),
    }


def build_insight_cards(db, user_id, job) -> list[dict]:
    """All insight cards that apply to this application (regardless of dismissal)."""
    cards: list[dict] = []

    match_result = get_latest_result(db, user_id, job.id)
    if match_result is not None:
        missing = _missing_skill_names(match_result)
        if missing:
            noun = "skill" if len(missing) == 1 else "skills"
            cards.append(
                _card(
                    INSIGHT_JD_MATCH_GAPS,
                    f"{len(missing)} missing {noun} for this role",
                    "Skills in the job description that your resume doesn't currently cover.",
                    missing,
                )
            )

    suggestions = _resume_suggestions(db, user_id, job.resume_id)
    if suggestions:
        cards.append(
            _card(
                INSIGHT_RESUME_SUGGESTIONS,
                "Resume suggestions for this application",
                "Suggestions from the latest analysis of the resume linked to this application.",
                suggestions,
            )
        )

    return cards


def get_dismissed_keys(db, user_id, job_id) -> list[str]:
    rows = (
        db.query(InsightDismissal.insight_key)
        .filter(
            InsightDismissal.user_id == user_id,
            InsightDismissal.job_application_id == job_id,
        )
        .all()
    )
    return [row[0] for row in rows]


def dismiss_insight(db, user_id, job_id, insight_key: str) -> list[str]:
    """Persist a dismissal for this user+application+key; returns updated keys."""
    existing = (
        db.query(InsightDismissal)
        .filter(
            InsightDismissal.user_id == user_id,
            InsightDismissal.job_application_id == job_id,
            InsightDismissal.insight_key == insight_key,
        )
        .first()
    )
    if existing is None:
        db.add(
            InsightDismissal(
                user_id=user_id,
                job_application_id=job_id,
                insight_key=insight_key,
            )
        )
        db.commit()
    return get_dismissed_keys(db, user_id, job_id)


def build_workspace_payload(db, user_id, job) -> dict:
    """The full workspace header payload: next action + non-dismissed insights."""
    dismissed = get_dismissed_keys(db, user_id, job.id)
    next_action = recommend_next_action_for_job(db, job)
    insights = [
        card
        for card in build_insight_cards(db, user_id, job)
        if card["key"] not in dismissed
    ]
    return {
        "next_action": next_action,
        "insights": insights,
        "dismissed": dismissed,
    }
