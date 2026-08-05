from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.core.limiter import limiter, _user_or_ip_key
from app.database import init_db, SessionLocal
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.body_size_limit import RequestBodySizeLimitMiddleware
from app.utils.exceptions import register_exception_handlers
from app.utils.response import success_response

logger = logging.getLogger(__name__)

# Import routers
from app.routers import auth, resume, ai, user
from app.routers.resume_import import router as resume_import_router
from app.routers.cover_letter import router as cover_letter_router
from app.routers.career import router as career_router
from app.routers.career_history import router as career_history_router
from app.career.roadmap_router import router as career_roadmap_router
from app.routers.job_tracker import router as job_tracker_router
from app.routers.analysis import router as analysis_router
from app.routers.jd_matching import router as jd_matching_router
from app.communication.router import router as communication_router
from app.communication.suggestions_router import router as suggestions_router
from app.interview_prep.router import router as interview_prep_router
from app.activity.router import router as activity_router
from app.analytics.router import router as analytics_router
from app.dashboard.router import router as dashboard_router

logger.info("AI provider=%s model=%s", settings.AI_PROVIDER, settings.GEMINI_MODEL)

scheduler = BackgroundScheduler()


def _run_suggestion_check():
    """Run the daily suggestion check in its own DB session."""
    db = SessionLocal()
    try:
        from app.communication.suggestions_service import check_and_create_suggestions
        count = check_and_create_suggestions(db)
        if count:
            logger.info(f"Created {count} follow-up suggestion(s)")
    except Exception as e:
        logger.error(f"Suggestion check failed: {e}")
    finally:
        db.close()



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    scheduler.add_job(
        _run_suggestion_check,
        "interval",
        days=1,
        id="follow_up_suggestion_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Suggestion scheduler started")
    yield
    # Shutdown
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="CareerCraftAI API",
    description="Backend API for CareerCraftAI - AI-powered resume builder",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# Request body size limit
app.add_middleware(RequestBodySizeLimitMiddleware)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(resume_import_router)
app.include_router(ai.router)
app.include_router(user.router)
app.include_router(cover_letter_router)
app.include_router(career_router)
app.include_router(career_history_router)
app.include_router(career_roadmap_router)
app.include_router(job_tracker_router)
app.include_router(analysis_router)
app.include_router(jd_matching_router)
app.include_router(suggestions_router)
app.include_router(communication_router)
app.include_router(interview_prep_router)
app.include_router(activity_router)
app.include_router(analytics_router)
app.include_router(dashboard_router)


# Health endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return success_response(
        data={
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        },
        message="Service is running",
    )


# Root endpoint
@app.get("/", tags=["Root"])
def root():
    """Root endpoint."""
    return success_response(
        data={
            "name": "CareerCraftAI API",
            "version": "1.0.0",
            "docs": "/docs",
        },
        message="Welcome to CareerCraftAI API",
    )
