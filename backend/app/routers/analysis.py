"""Analysis API router with persistence, caching, and version awareness."""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.resume import Resume
from app.models.user import User
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.schemas.resume_analysis import (
    AnalysisCacheCheck,
    ReAnalysisRequest,
    ResumeAnalysisHistoryResponse,
    ResumeAnalysisListItem,
    ResumeAnalysisResponse,
    ResumeAnalysisStaleStatus,
)
from app.main import limiter
from app.services.analysis_persistence_service import (
    acquire_analysis_lock,
    check_cache,
    get_analysis_by_id,
    get_analysis_history,
    get_latest_analysis,
    is_analysis_in_progress,
    mark_stale_analyses,
    release_analysis_lock,
    save_analysis,
    _extract_scores,
)
from app.services.analysis_service import analyze_resume
from app.utils.exceptions import ValidationException
from app.utils.resume_serializer import serialize_resume

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


def _build_analysis_response(result: dict) -> AnalysisResponse:
    return AnalysisResponse(
        status="success",
        analyzed_at=datetime.utcnow().isoformat(),
        deterministic=result["deterministic"],
        quality_report=result.get("quality_report"),
        ats_analysis=result.get("ats_analysis"),
        skill_analysis=result.get("skill_analysis"),
        strengths_weaknesses=result.get("strengths_weaknesses"),
        deep_analysis=result.get("deep_analysis"),
        recommendations=result.get("recommendations", []),
        total_recommendations=result.get("total_recommendations", 0),
        high_priority_recommendations=result.get("high_priority_recommendations", 0),
    )


def _determine_source(enable_ai: bool) -> str:
    return "full" if enable_ai else "deterministic"


# ---------------------------------------------------------------------------
# POST /analyze — existing inline endpoint, enhanced with caching
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=AnalysisResponse)
@limiter.limit(f"{settings.RATE_LIMIT_ANALYSIS};{settings.RATE_LIMIT_ANALYSIS_DAILY}")
def run_analysis(
    request: Request,
    analysis_req: AnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Run resume analysis with optional caching.

    If resume_id is provided the result is cached.  A cached result is
    returned directly when it exists and is fresh (same resume.version).
    Set ?force=1 or include force=true in the body to bypass cache.
    """
    if not analysis_req.resume or not isinstance(analysis_req.resume, dict):
        raise ValidationException("Resume data must be a non-empty object")

    resume_id = analysis_req.resume_id
    enable_ai = analysis_req.enable_ai
    source = _determine_source(enable_ai)

    logger.info(
        "Analysis requested for user %s (resume_id=%s, ai=%s)",
        current_user.id, resume_id, enable_ai,
    )

    # --- Cache check ---
    if resume_id is not None:
        resume_db = (
            db.query(Resume)
            .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
            .first()
        )
        if resume_db is None:
            raise ValidationException("Resume not found or access denied")

        resume_version = resume_db.version
        cached, stale, record = check_cache(db, resume_id, current_user.id, resume_version)

        if cached and not stale:
            logger.info(
                "Cache HIT for resume_id=%s version=%s",
                resume_id, resume_version,
            )
            result = record.analysis_json
            result["_cached"] = True
            result["_analysis_id"] = record.id
            return _build_analysis_response(result)

        if cached and stale:
            logger.info(
                "Cache STALE for resume_id=%s (analysis version=%s < resume version=%s)",
                resume_id, record.resume_version, resume_version,
            )
    else:
        resume_version = 0

    # --- Concurrent request guard ---
    if resume_id is not None:
        if not acquire_analysis_lock(resume_id):
            raise HTTPException(
                status_code=409,
                detail="Analysis already in progress for this resume",
            )
        try:
            result = _run_and_persist(resume_id, analysis_req, current_user, db, resume_version, source)
        finally:
            release_analysis_lock(resume_id)
    else:
        result = analyze_resume(
            analysis_req.resume,
            enable_ai=enable_ai,
            resume_id=None,
        )
        result["_cached"] = False
        result["_analysis_id"] = None

    return _build_analysis_response(result)


def _run_and_persist(resume_id, analysis_req, current_user, db, resume_version, source):
    """Run analysis and persist the result."""
    try:
        result = analyze_resume(
            analysis_req.resume,
            enable_ai=analysis_req.enable_ai,
            resume_id=resume_id,
        )
    except Exception as e:
        logger.exception("Analysis failed for resume_id=%s user=%s", resume_id, current_user.id)
        raise ValidationException(f"Analysis failed: {str(e)}")

    scores = _extract_scores(result)
    record = save_analysis(
        db=db,
        user_id=current_user.id,
        resume_id=resume_id,
        resume_version=resume_version,
        source=source,
        analysis_json=result,
        scores_json=scores,
    )

    # Mark older analyses as stale
    mark_stale_analyses(db, resume_id, current_user.id, resume_version)

    result["_cached"] = False
    result["_analysis_id"] = record.id
    result["_analysis_version"] = resume_version

    logger.info(
        "Analysis persisted id=%s for resume_id=%s version=%s",
        record.id, resume_id, resume_version,
    )
    return result


# ---------------------------------------------------------------------------
# GET /resume/{resume_id}/latest — retrieve cached latest analysis
# ---------------------------------------------------------------------------


@router.get("/resume/{resume_id}/latest", response_model=AnalysisCacheCheck)
def get_latest_cached_analysis(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the latest cached analysis for a resume.

    Returns whether a cache entry exists, whether it is stale,
    and the analysis data if available.
    """
    resume_db = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume_db is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_version = resume_db.version
    cached, stale, record = check_cache(db, resume_id, current_user.id, resume_version)

    if not record:
        return AnalysisCacheCheck(cached=False, stale=False, analysis=None)

    response_data = ResumeAnalysisResponse(
        id=record.id,
        resume_id=record.resume_id,
        resume_version=record.resume_version,
        source=record.source,
        analysis_json=record.analysis_json,
        scores_json=record.scores_json,
        job_description_id=record.job_description_id,
        is_stale=bool(record.is_stale) or stale,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )

    return AnalysisCacheCheck(
        cached=cached,
        stale=stale or bool(record.is_stale),
        analysis=response_data,
    )


# ---------------------------------------------------------------------------
# POST /resume/{resume_id}/analyze — persisted analysis from DB resume
# ---------------------------------------------------------------------------


class _AnalyzeDbRequest(BaseModel):
    enable_ai: bool = Field(False, description="Enable AI deep analysis")


@router.post("/resume/{resume_id}/analyze", response_model=AnalysisResponse)
@limiter.limit(f"{settings.RATE_LIMIT_ANALYSIS};{settings.RATE_LIMIT_ANALYSIS_DAILY}")
def analyze_resume_from_db(
    request: Request,
    resume_id: int,
    analysis_req: _AnalyzeDbRequest = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Load a resume from the database, run analysis, and persist."""
    resume_db = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume_db is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_data = serialize_resume(resume_db)
    enable_ai = analysis_req.enable_ai if analysis_req else False
    source = _determine_source(enable_ai)
    resume_version = resume_db.version

    if is_analysis_in_progress(resume_id):
        raise HTTPException(
            status_code=409,
            detail="Analysis already in progress for this resume",
        )

    if not acquire_analysis_lock(resume_id):
        raise HTTPException(status_code=409, detail="Analysis already in progress")
    try:
        try:
            result = analyze_resume(
                resume_data,
                enable_ai=enable_ai,
                resume_id=resume_id,
            )
        except Exception as e:
            logger.exception("Analysis failed for resume_id=%s", resume_id)
            raise ValidationException(f"Analysis failed: {str(e)}")

        scores = _extract_scores(result)
        record = save_analysis(
            db=db,
            user_id=current_user.id,
            resume_id=resume_id,
            resume_version=resume_version,
            source=source,
            analysis_json=result,
            scores_json=scores,
        )
        mark_stale_analyses(db, resume_id, current_user.id, resume_version)

        result["_cached"] = False
        result["_analysis_id"] = record.id
    finally:
        release_analysis_lock(resume_id)

    return _build_analysis_response(result)


# ---------------------------------------------------------------------------
# POST /resume/{resume_id}/re-analyze — force re-analysis
# ---------------------------------------------------------------------------


@router.post("/resume/{resume_id}/re-analyze", response_model=AnalysisResponse)
@limiter.limit(f"{settings.RATE_LIMIT_ANALYSIS};{settings.RATE_LIMIT_ANALYSIS_DAILY}")
def re_analyze_resume(
    request: Request,
    resume_id: int,
    analysis_req: ReAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Force re-analysis of a resume, ignoring cache."""
    resume_db = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume_db is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_data = serialize_resume(resume_db)
    enable_ai = analysis_req.enable_ai
    source = _determine_source(enable_ai)
    resume_version = resume_db.version

    if not acquire_analysis_lock(resume_id):
        raise HTTPException(status_code=409, detail="Analysis already in progress")
    try:
        try:
            result = analyze_resume(
                resume_data,
                enable_ai=enable_ai,
                resume_id=resume_id,
            )
        except Exception as e:
            logger.exception("Re-analysis failed for resume_id=%s", resume_id)
            raise ValidationException(f"Re-analysis failed: {str(e)}")

        scores = _extract_scores(result)
        record = save_analysis(
            db=db,
            user_id=current_user.id,
            resume_id=resume_id,
            resume_version=resume_version,
            source=source,
            analysis_json=result,
            scores_json=scores,
        )
        mark_stale_analyses(db, resume_id, current_user.id, resume_version)

        result["_cached"] = False
        result["_analysis_id"] = record.id
    finally:
        release_analysis_lock(resume_id)

    return _build_analysis_response(result)


# ---------------------------------------------------------------------------
# GET /{analysis_id} — get a specific analysis by ID
# ---------------------------------------------------------------------------


@router.get("/{analysis_id}", response_model=ResumeAnalysisResponse)
def get_analysis_record(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve a specific analysis record by ID."""
    record = get_analysis_by_id(db, analysis_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    resume_db = (
        db.query(Resume)
        .filter(Resume.id == record.resume_id)
        .first()
    )
    is_stale = bool(record.is_stale)
    if resume_db and resume_db.version > record.resume_version:
        is_stale = True

    return ResumeAnalysisResponse(
        id=record.id,
        resume_id=record.resume_id,
        resume_version=record.resume_version,
        source=record.source,
        analysis_json=record.analysis_json,
        scores_json=record.scores_json,
        job_description_id=record.job_description_id,
        is_stale=is_stale,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


# ---------------------------------------------------------------------------
# GET /resume/{resume_id}/history — analysis history for a resume
# ---------------------------------------------------------------------------


@router.get("/resume/{resume_id}/history", response_model=ResumeAnalysisHistoryResponse)
def get_analysis_history_endpoint(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """Get analysis history for a resume."""
    resume_db = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume_db is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    records = get_analysis_history(db, resume_id, current_user.id, limit=limit)

    items = []
    for rec in records:
        is_stale = bool(rec.is_stale) or resume_db.version > rec.resume_version
        items.append(
            ResumeAnalysisListItem(
                id=rec.id,
                resume_id=rec.resume_id,
                resume_version=rec.resume_version,
                source=rec.source,
                is_stale=is_stale,
                created_at=rec.created_at,
            )
        )

    return ResumeAnalysisHistoryResponse(
        analyses=items,
        total=len(items),
        current_version=resume_db.version,
    )


# ---------------------------------------------------------------------------
# GET /resume/{resume_id}/stale — check stale status
# ---------------------------------------------------------------------------


@router.get("/resume/{resume_id}/stale", response_model=ResumeAnalysisStaleStatus)
def get_stale_status(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Check if the cached analysis for a resume is stale."""
    resume_db = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume_db is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_version = resume_db.version
    latest = get_latest_analysis(db, resume_id, current_user.id)

    if latest is None:
        return ResumeAnalysisStaleStatus(
            resume_id=resume_id,
            resume_version=resume_version,
            has_cached=False,
            message="No cached analysis found for this resume",
        )

    is_stale = resume_version > latest.resume_version or bool(latest.is_stale)

    return ResumeAnalysisStaleStatus(
        resume_id=resume_id,
        resume_version=resume_version,
        analysis_version=latest.resume_version,
        is_stale=is_stale,
        has_cached=True,
        analysis_id=latest.id,
        message="Analysis is stale, re-analyze recommended" if is_stale else "Analysis is up to date",
    )
