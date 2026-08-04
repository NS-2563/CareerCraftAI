"""Today's Focus: surface the single best signal-backed Career Coach recommendation.

This is NOT a new recommendation algorithm. It reuses the deterministic signal
counts produced by ``recommendation_signals.enrich_priority_recommendations``
(stored inside each Career Report's ``skill_gap.priority``) and simply picks the
top one: highest ``supported_signals / total_possible_signals`` ratio, tie-broken
by ease of categorization.

The category label is a coarse, real classification derived from which signal
type dominates the recommendation's own reasons — never a fabricated time/effort
estimate:

- "New skill"       - dominated by the JD missing-skill signal ("Missing in N of M saved job matches")
- "Resume wording"  - dominated by the resume-analysis signal ("Flagged ... resume analysis")
- "Practice"        - dominated by the interview-weakness signal ("weakest interview area")
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.career_report import CareerReport

logger = logging.getLogger(__name__)

CATEGORY_NEW_SKILL = "New skill"
CATEGORY_RESUME_WORDING = "Resume wording"
CATEGORY_PRACTICE = "Practice"

# Tie-break order when multiple signal types are equally represented.
_CATEGORY_PRECEDENCE = [
    CATEGORY_NEW_SKILL,
    CATEGORY_RESUME_WORDING,
    CATEGORY_PRACTICE,
]

# Keyword -> category lookup over Phase 2's exact reason templates.
_CATEGORY_MATCHERS = (
    (CATEGORY_NEW_SKILL, ("saved job matches",)),
    (CATEGORY_RESUME_WORDING, ("resume analysis",)),
    (CATEGORY_PRACTICE, ("weakest interview",)),
)


def _category_for_reason(reason: str) -> Optional[str]:
    """Map one Phase-2 reason string back to its signal category (or None)."""
    text = (reason or "").lower()
    for category, keywords in _CATEGORY_MATCHERS:
        if any(keyword in text for keyword in keywords):
            return category
    return None


def categorize_recommendation(recommendation: dict) -> Optional[dict]:
    """Classify one Phase-2 recommendation into an honest coarse category.

    Counts which signal type dominates the recommendation's real reasons and
    assigns the matching category. A skill whose only backing is roadmap
    consistency (no JD/resume/interview signal) falls back to "New skill",
    because the roadmap is recommending that the user learn it.
    """
    reasons = [str(r) for r in (recommendation.get("reasons") or [])]

    counts = {}
    for reason in reasons:
        category = _category_for_reason(reason)
        if category:
            counts[category] = counts.get(category, 0) + 1

    if counts:
        category = max(
            _CATEGORY_PRECEDENCE,
            key=lambda c: counts.get(c, 0),
        )
    else:
        category = CATEGORY_NEW_SKILL

    return {
        "skill": recommendation.get("skill"),
        "category": category,
        "supported_signals": recommendation.get("supported_signals"),
        "total_possible_signals": recommendation.get("total_possible_signals"),
        "reasons": reasons,
    }


def _priority_entries(report: CareerReport) -> list:
    """Extract the enriched priority entries from a stored report, safely."""
    report_json = report.report_json or {}
    if not isinstance(report_json, dict):
        return []
    skill_gap = report_json.get("skill_gap") or {}
    if not isinstance(skill_gap, dict):
        return []
    priority = skill_gap.get("priority") or []
    if not isinstance(priority, list):
        return []
    return priority


def get_today_focus(db: Session, user_id: int) -> Optional[dict]:
    """Return the single best recommendation, or None when there is none real.

    Backward-compatible wrapper: the top of ``get_today_focus_items``.
    """
    items = get_today_focus_items(db, user_id, limit=1)
    return items[0] if items else None


def get_today_focus_items(db: Session, user_id: int, limit: int = 3) -> list:
    """Return the top ``limit`` recommendations by real signal count.

    Selection reuses Phase 2's signal counts directly:
    1. Primary: highest supported/total ratio.
    2. Tie-break: easiest to categorize (a single dominant signal category beats
       a mixed one), then higher supported count, then alphabetical.

    Returns an empty list when the user has no career report, no enriched
    priority entries, or no candidate with supported signals > 0 (nothing real
    to surface — the "you're all caught up" state). Zero-signal candidates are
    always dropped; a partial top-3 (fewer than 3 real candidates) is returned
    honestly rather than padded.
    """
    latest = (
        db.query(CareerReport)
        .filter(CareerReport.user_id == user_id)
        .order_by(CareerReport.created_at.desc(), CareerReport.id.desc())
        .first()
    )
    if latest is None:
        return []

    candidates = []
    for item in _priority_entries(latest):
        if not isinstance(item, dict):
            continue
        skill = item.get("skill")
        supported = item.get("supported_signals")
        total = item.get("total_possible_signals")
        if not isinstance(skill, str) or not skill.strip():
            continue
        if not isinstance(supported, (int, float)) or not isinstance(total, (int, float)):
            continue
        total = float(total)
        if total <= 0:
            continue

        categorized = categorize_recommendation(item)
        category_reason_count = sum(
            1 for r in categorized["reasons"] if _category_for_reason(r)
        )
        candidates.append({
            "ratio": float(supported) / total,
            "category_reason_count": category_reason_count,
            "supported": float(supported),
            "skill": skill.strip(),
            "payload": categorized,
        })

    if not candidates:
        return []

    def sort_key(candidate):
        # Easiest to categorize = exactly one dominant category signal.
        ease = (
            0
            if candidate["category_reason_count"] == 1
            else 1 if candidate["category_reason_count"] == 0 else 2
        )
        return (
            -candidate["ratio"],
            ease,
            -candidate["supported"],
            candidate["skill"].lower(),
        )

    candidates.sort(key=sort_key)

    # Drop zero-signal candidates (nothing real to surface) — the "all caught up" state.
    ranked = [c["payload"] for c in candidates if float(c["payload"].get("supported_signals", 0)) > 0]

    return ranked[:limit]
