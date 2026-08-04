"""JD Match persistence — store match results so they can be shown per application.

Matching itself stays stateless in ``jd_match_service``; this module adds the
optional persistence layer on top (when a request is linked to a job
application).
"""

import json
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.jd_match_result import JDMatchResult


def _serialize(items) -> str:
    """Serialize a list of skill items (or fall back to plain strings) to JSON."""
    return json.dumps(items or [])


def persist_match_result(
    db: Session,
    user_id: int,
    job_application_id: int,
    resume_id: Optional[int],
    result: dict,
    enable_ai: bool,
) -> JDMatchResult:
    """Create a stored JDMatchResult from a match result dict.

    Callers are responsible for ownership-checking ``job_application_id``.
    """
    record = JDMatchResult(
        user_id=user_id,
        job_application_id=job_application_id,
        resume_id=resume_id,
        match_score=float(result.get("overall_match_score", 0)),
        matched_skills=_serialize(result.get("matched_skills", [])),
        missing_skills=_serialize(result.get("missing_skills", [])),
        used_ai=bool(enable_ai),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_latest_result(
    db: Session,
    user_id: int,
    job_application_id: int,
) -> Optional[JDMatchResult]:
    """Return the most recent match result for an application owned by the user."""
    return (
        db.query(JDMatchResult)
        .filter(
            JDMatchResult.user_id == user_id,
            JDMatchResult.job_application_id == job_application_id,
        )
        .order_by(JDMatchResult.created_at.desc(), JDMatchResult.id.desc())
        .first()
    )


def list_results(
    db: Session,
    user_id: int,
    job_application_id: int,
    limit: int = 20,
) -> List[JDMatchResult]:
    """Return recent match results for an application, newest first."""
    return (
        db.query(JDMatchResult)
        .filter(
            JDMatchResult.user_id == user_id,
            JDMatchResult.job_application_id == job_application_id,
        )
        .order_by(JDMatchResult.created_at.desc(), JDMatchResult.id.desc())
        .limit(limit)
        .all()
    )
