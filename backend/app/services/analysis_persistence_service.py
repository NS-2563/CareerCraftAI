"""Analysis persistence and caching service.

Provides CRUD operations for ResumeAnalysis records including
stale detection, cache lookups, and concurrent request prevention.
"""
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis

logger = logging.getLogger(__name__)

# In-memory lock to prevent duplicate concurrent analysis for the same resume
_analysis_locks: Dict[int, threading.Lock] = {}
_locks_lock = threading.Lock()


def _get_resume_lock(resume_id: int) -> threading.Lock:
    with _locks_lock:
        if resume_id not in _analysis_locks:
            _analysis_locks[resume_id] = threading.Lock()
        return _analysis_locks[resume_id]


def is_analysis_in_progress(resume_id: int) -> bool:
    """Check if an analysis is currently running for this resume."""
    lock = _get_resume_lock(resume_id)
    acquired = lock.acquire(blocking=False)
    if acquired:
        lock.release()
        return False
    return True


def acquire_analysis_lock(resume_id: int) -> bool:
    """Try to acquire the analysis lock for a resume.

    Returns True if the lock was acquired (no concurrent analysis running).
    Returns False if another analysis is already in progress.
    """
    lock = _get_resume_lock(resume_id)
    acquired = lock.acquire(blocking=False)
    return acquired


def release_analysis_lock(resume_id: int) -> None:
    """Release the analysis lock for a resume."""
    lock = _get_resume_lock(resume_id)
    lock.release()


def get_latest_analysis(
    db: Session,
    resume_id: int,
    user_id: int,
) -> Optional[ResumeAnalysis]:
    """Get the most recent analysis for a resume, checking ownership."""
    return (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.resume_id == resume_id,
            ResumeAnalysis.user_id == user_id,
        )
        .order_by(ResumeAnalysis.id.desc())
        .first()
    )


def get_analysis_by_id(
    db: Session,
    analysis_id: int,
    user_id: int,
) -> Optional[ResumeAnalysis]:
    """Get a specific analysis by ID, with ownership check."""
    return (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.id == analysis_id,
            ResumeAnalysis.user_id == user_id,
        )
        .first()
    )


def get_analysis_history(
    db: Session,
    resume_id: int,
    user_id: int,
    limit: int = 20,
) -> List[ResumeAnalysis]:
    """Get analysis history for a resume."""
    return (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.resume_id == resume_id,
            ResumeAnalysis.user_id == user_id,
        )
        .order_by(ResumeAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )


def check_cache(
    db: Session,
    resume_id: int,
    user_id: int,
    resume_version: int,
) -> Tuple[bool, bool, Optional[ResumeAnalysis]]:
    """Check if a fresh cached analysis exists.

    Returns:
        Tuple of (cached_exists, is_stale, analysis_record)
    """
    latest = get_latest_analysis(db, resume_id, user_id)
    if latest is None:
        return False, False, None

    if resume_version > latest.resume_version:
        return True, True, latest

    return True, False, latest


def save_analysis(
    db: Session,
    user_id: int,
    resume_id: int,
    resume_version: int,
    source: str,
    analysis_json: Dict[str, Any],
    scores_json: Optional[Dict[str, Any]] = None,
    job_description_id: Optional[int] = None,
) -> ResumeAnalysis:
    """Save a new analysis record."""
    record = ResumeAnalysis(
        user_id=user_id,
        resume_id=resume_id,
        resume_version=resume_version,
        source=source,
        analysis_json=analysis_json,
        scores_json=scores_json,
        job_description_id=job_description_id,
        is_stale=0,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        "Saved analysis id=%s for resume_id=%s version=%s source=%s",
        record.id, resume_id, resume_version, source,
    )
    return record


def mark_stale_analyses(
    db: Session,
    resume_id: int,
    user_id: int,
    current_version: int,
) -> int:
    """Mark all analyses for a resume as stale when resume is updated.

    Returns the number of records marked stale.
    """
    count = (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.resume_id == resume_id,
            ResumeAnalysis.user_id == user_id,
            ResumeAnalysis.resume_version < current_version,
            ResumeAnalysis.is_stale == 0,
        )
        .update({"is_stale": 1}, synchronize_session=False)
    )
    if count > 0:
        db.commit()
        logger.info("Marked %d stale analyses for resume_id=%s", count, resume_id)
    return count


def delete_analysis(
    db: Session,
    analysis_id: int,
    user_id: int,
) -> bool:
    """Delete an analysis record with ownership check."""
    record = get_analysis_by_id(db, analysis_id, user_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def _extract_scores(analysis_json: Dict[str, Any]) -> Dict[str, Any]:
    """Extract top-level scores from analysis result for quick lookup."""
    scores = {}
    det = analysis_json.get("deterministic") or {}
    quality = analysis_json.get("quality_report") or {}
    ats = analysis_json.get("ats_analysis") or {}
    sw = analysis_json.get("strengths_weaknesses") or {}
    recs = analysis_json.get("recommendations") or []

    overall = det.get("overall_quality_score") or {}
    scores["overall_score"] = overall.get("overall_score", 0)
    scores["quality_score"] = quality.get("overall_score", 0)
    scores["ats_score"] = ats.get("overall_ats_score", 0)
    scores["completeness_score"] = det.get("completeness", {}).get("overall_completeness_score", 0)
    scores["strength_count"] = sw.get("strength_count", 0)
    scores["weakness_count"] = sw.get("weakness_count", 0)
    scores["recommendation_count"] = len(recs)
    scores["high_priority_count"] = analysis_json.get("high_priority_recommendations", 0)

    return scores
