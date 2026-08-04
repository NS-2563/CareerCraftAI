"""User-set progress status for Career Coach roadmap recommendations.

Task statuses live in ``roadmap_task_statuses`` keyed by ``(user_id,
normalized_skill)`` — one row per user per recommendation. Because identity is
the normalized skill name (not the position in the list), a user's
in-progress/done state survives a roadmap refresh that regenerates the
underlying recommendation set: a re-recommended skill keeps its status and a
skill that is no longer recommended simply stays stored (harmless) until it is
recommended again.
"""

import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

TASK_STATUSES = ("not_started", "in_progress", "done")


def _skill_key(value: str) -> str:
    """Normalize a skill name for identity matching across regenerations."""
    return (value or "").strip().lower()


def ensure_task_rows(
    db: Session,
    user_id: int,
    skills: List[str],
) -> Dict[str, "RoadmapTaskStatus"]:
    """Get-or-create a status row per skill, returning {skill_key: row}.

    Existing rows keep their user-set status (that is the whole point of
    persistence); brand-new skills start as ``not_started``.
    """
    from app.models.roadmap_task_status import RoadmapTaskStatus

    rows: Dict[str, RoadmapTaskStatus] = {}
    for skill in skills or []:
        name = str(skill).strip() if skill is not None else ""
        if not name:
            continue
        key = _skill_key(name)
        row = (
            db.query(RoadmapTaskStatus)
            .filter(
                RoadmapTaskStatus.user_id == user_id,
                RoadmapTaskStatus.skill_key == key,
            )
            .first()
        )
        if row is None:
            row = RoadmapTaskStatus(
                user_id=user_id,
                skill=name,
                skill_key=key,
                status="not_started",
            )
            db.add(row)
            db.flush()
        rows[key] = row

    db.commit()
    return rows


def attach_task_statuses(
    db: Session,
    user_id: int,
    report: dict,
) -> dict:
    """Enrich each ``skill_gap.priority`` recommendation with its task identity.

    Adds ``task_id``, ``task_status``, and ``task_status_settable`` to every
    enriched (dict) priority entry, plus a deterministic ``confidence`` bucket
    for reports saved before that field existed. Mutates ``report`` in place
    and returns it. Plain-string entries are left untouched.
    """
    from app.career.services.recommendation_signals import confidence_label

    skill_gap = (report or {}).get("skill_gap") or {}
    if not isinstance(skill_gap, dict):
        return report
    priority = skill_gap.get("priority") or []
    if not priority:
        return report

    skills: List[str] = []
    for item in priority:
        if isinstance(item, dict) and item.get("skill"):
            skills.append(item["skill"])
        elif isinstance(item, str) and item.strip():
            skills.append(item)

    if not skills:
        return report

    rows = ensure_task_rows(db, user_id, skills)

    for item in priority:
        if not isinstance(item, dict):
            continue
        name = item.get("skill")
        if not name:
            continue
        row = rows.get(_skill_key(name))
        if row is None:
            continue
        item["task_id"] = row.id
        item["task_status"] = row.status
        item["task_status_settable"] = True
        if "confidence" not in item:
            item["confidence"] = confidence_label(
                int(item.get("supported_signals") or 0),
                int(item.get("total_possible_signals") or 0),
            )

    return report


def get_task_status(
    db: Session,
    task_id: int,
    user_id: int,
) -> Optional["RoadmapTaskStatus"]:
    """Fetch one task row, ownership-scoped, or None."""
    from app.models.roadmap_task_status import RoadmapTaskStatus

    return (
        db.query(RoadmapTaskStatus)
        .filter(
            RoadmapTaskStatus.id == task_id,
            RoadmapTaskStatus.user_id == user_id,
        )
        .first()
    )


def set_task_status(
    db: Session,
    task_id: int,
    user_id: int,
    status: str,
) -> Optional["RoadmapTaskStatus"]:
    """Set a task's status (ownership-checked). Returns None when not found.

    Raises ``ValueError`` for statuses outside the allowed set.
    """
    if status not in TASK_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. Allowed: {', '.join(TASK_STATUSES)}."
        )

    row = get_task_status(db, task_id, user_id)
    if row is None:
        return None

    row.status = status
    db.commit()
    db.refresh(row)
    return row
