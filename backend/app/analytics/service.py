import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.models import ScoreSnapshot

logger = logging.getLogger(__name__)


def _norm_skill(value: str) -> str:
    """Lowercase/whitespace-normalize a skill name for set comparison."""
    return (value or "").strip().lower()


def _skill_name_map(skills) -> dict:
    """Map normalized skill name -> original casing, keeping first occurrence.

    Accepts a list of skill dicts/strings or a dict already normalized this way.
    """
    mapping = {}

    if isinstance(skills, dict):
        for norm_key, original in skills.items():
            name = original if isinstance(original, str) else norm_key
            if isinstance(name, str) and name.strip():
                key = _norm_skill(norm_key)
                if key and key not in mapping:
                    mapping[key] = name.strip()
        return mapping

    for skill in skills or []:
        name = skill if isinstance(skill, str) else (skill.get("name") if isinstance(skill, dict) else None)
        if not isinstance(name, str) or not name.strip():
            continue
        key = _norm_skill(name)
        if key and key not in mapping:
            mapping[key] = name.strip()
    return mapping


def extract_resume_content(resume_data) -> Optional[dict]:
    """Extract the lightweight content captured alongside a score snapshot.

    Returns ``{"skills": [...], "summary": "..."}`` or ``None`` when the input
    is unusable. Handles skills as a list of dicts/strings or a JSON string,
    and a summary at top level or nested under ``personal``.
    """
    if not isinstance(resume_data, dict):
        return None

    skills = resume_data.get("skills")
    if isinstance(skills, str):
        try:
            skills = json.loads(skills)
        except (TypeError, ValueError):
            skills = None

    summary = resume_data.get("summary")
    if not isinstance(summary, str):
        personal = resume_data.get("personal")
        if isinstance(personal, dict):
            summary = personal.get("summary") or personal.get("professionalSummary")

    return {
        "skills": list(_skill_name_map(skills).values()),
        "summary": (summary or "").strip(),
    }


def compute_content_diff(from_content: dict, to_content: dict) -> dict:
    """Deterministically compare two captured snapshot contents.

    Returns exactly the computed facts: which skills were added/removed (by
    normalized name, preserving the snapshot's original casing), whether the
    summary text changed, and the summary word-count delta. No inference.
    """
    from_map = _skill_name_map(from_content.get("skills") or [])
    to_map = _skill_name_map(to_content.get("skills") or [])

    from_keys = set(from_map.keys())
    to_keys = set(to_map.keys())

    added = [to_map[key] for key in sorted(to_keys - from_keys)]
    removed = [from_map[key] for key in sorted(from_keys - to_keys)]

    from_summary = (from_content.get("summary") or "").strip()
    to_summary = (to_content.get("summary") or "").strip()

    def _words(text):
        return len(text.split()) if text else 0

    return {
        "skills_added": added,
        "skills_removed": removed,
        "summary_changed": from_summary != to_summary,
        "summary_word_delta": _words(to_summary) - _words(from_summary),
    }


def jd_keywords_now_covered(
    db: Session,
    user_id: int,
    resume_id: int,
    added_skills,
) -> list:
    """Return added skills that now cover previously-missing JD-match keywords.

    Cross-references the added skills against the ``missing_skills`` recorded in
    the user's stored JD-match results for this resume. This is a real, computed
    keyword-overlap check against concrete stored data - never an AI assertion.
    """
    from app.models.jd_match_result import JDMatchResult

    rows = (
        db.query(JDMatchResult)
        .filter(
            JDMatchResult.user_id == user_id,
            JDMatchResult.resume_id == resume_id,
        )
        .all()
    )

    missing = {}
    for row in rows:
        raw = row.missing_skills
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if not isinstance(parsed, list):
            continue
        for item in parsed:
            name = item.get("name") if isinstance(item, dict) else item
            if not isinstance(name, str) or not name.strip():
                continue
            key = _norm_skill(name)
            if key and key not in missing:
                missing[key] = name.strip()

    if not missing:
        return []

    added_keys = {_norm_skill(s) for s in (added_skills or []) if isinstance(s, str)}
    return [missing[key] for key in sorted(added_keys & set(missing.keys()))]


class AnalyticsService:

    DEDUP_INTERVAL_HOURS = 24

    @staticmethod
    def record_snapshot(
        db: Session,
        user_id: int,
        metric_type: str,
        value: float,
        resume_id: Optional[int] = None,
        content: Optional[dict] = None,
    ) -> None:
        try:
            query = db.query(ScoreSnapshot).filter(
                ScoreSnapshot.user_id == user_id,
                ScoreSnapshot.metric_type == metric_type,
            )
            if resume_id is not None:
                query = query.filter(ScoreSnapshot.resume_id == resume_id)
            latest = query.order_by(ScoreSnapshot.recorded_at.desc()).first()

            if latest is not None:
                is_same_value = abs(latest.value - value) < 0.001
                is_recent = (
                    latest.recorded_at
                    and latest.recorded_at >= datetime.utcnow() - timedelta(hours=AnalyticsService.DEDUP_INTERVAL_HOURS)
                )
                if is_same_value and is_recent:
                    return

            snapshot = ScoreSnapshot(
                user_id=user_id,
                resume_id=resume_id,
                metric_type=metric_type,
                value=value,
                content_json=content,
            )
            db.add(snapshot)
            db.commit()
        except Exception:
            logger.warning(
                "Failed to record snapshot user_id=%s metric=%s value=%s resume_id=%s",
                user_id, metric_type, value, resume_id,
                exc_info=True,
            )

    @staticmethod
    def get_snapshot(
        db: Session,
        user_id: int,
        snapshot_id: int,
    ) -> Optional[ScoreSnapshot]:
        """Fetch a single snapshot owned by the user, or None."""
        return (
            db.query(ScoreSnapshot)
            .filter(
                ScoreSnapshot.id == snapshot_id,
                ScoreSnapshot.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def get_history(
        db: Session,
        user_id: int,
        metric_type: str,
        limit: int = 100,
        descending: bool = False,
        resume_id: Optional[int] = None,
    ) -> list[ScoreSnapshot]:
        """Return score snapshots for a metric.

        Ordered oldest-first by default; pass ``descending=True`` for newest-first
        (useful when fetching a small ``limit`` of the latest values). Pass
        ``resume_id`` to scope to a single resume's history.
        """
        order = (
            (ScoreSnapshot.recorded_at.desc(), ScoreSnapshot.id.desc())
            if descending
            else (ScoreSnapshot.recorded_at.asc(), ScoreSnapshot.id.asc())
        )
        query = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.user_id == user_id,
            ScoreSnapshot.metric_type == metric_type,
        )
        if resume_id is not None:
            query = query.filter(ScoreSnapshot.resume_id == resume_id)
        return (
            query
            .order_by(*order)
            .limit(limit)
            .all()
        )
