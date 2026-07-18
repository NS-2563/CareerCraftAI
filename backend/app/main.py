from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.utils.exceptions import register_exception_handlers
from app.utils.response import success_response

# Import routers
from app.auth.router import router as auth_router

from app.resume.router import router as resume_router
from app.routers.ai import router as ai_router
from app.routers.user import router as user_router
from app.routers.cover_letter import router as cover_letter_router
from app.routers.career import router as career_router
from app.routers.career_history import router as career_history_router
from app.routers.job_tracker import router as job_tracker_router




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    yield
    # Shutdown


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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(ai_router)
app.include_router(user_router)
app.include_router(cover_letter_router)
app.include_router(career_router)
app.include_router(career_history_router)
app.include_router(job_tracker_router)


# Health endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return success_response(
        data={
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
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
