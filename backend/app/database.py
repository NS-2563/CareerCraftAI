from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings


_is_sqlite = "sqlite" in settings.DATABASE_URL

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    echo=False,
)

if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _enable_sqlite_wal(dbapi_connection, connection_record):
        """Enable WAL journal mode to reduce write-lock contention."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Database dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and run pending schema migrations."""

    # Import models in correct order to resolve relationships
    from app.models.user import User
    from app.models.resume import Resume
    from app.models.career_report import CareerReport
    from app.models.job_application import JobApplication
    from app.models.resume_analysis import ResumeAnalysis
    from app.models.cover_letter import CoverLetter
    from app.communication.models import CommunicationMessage, CommunicationSuggestion
    from app.interview_prep.models import InterviewSession
    from app.activity.models import ActivityEvent
    from app.analytics.models import ScoreSnapshot
    from app.models.jd_match_result import JDMatchResult
    from app.models.roadmap_task_status import RoadmapTaskStatus
    from app.models.insight_dismissal import InsightDismissal

    Base.metadata.create_all(bind=engine)

    _run_pending_migrations()


def _run_pending_migrations():
    """Apply any schema changes that create_all() cannot handle (e.g., adding columns to existing tables)."""
    for module_name, label in [
        ("_003_add_missing_columns", "003: added columns"),
        ("_004_add_user_id_indexes", "004: added indexes"),
        ("_005_add_interview_sessions", "005: added interview_sessions table"),
        ("_006_add_job_role_normalized", "006: added job_role_normalized column"),
        ("_007_add_activity_events", "007: added activity_events table"),
        ("_008_add_score_snapshots", "008: added score_snapshots table"),
        ("_009_add_communication_direction", "009: added communication direction columns"),
        ("_010_add_cover_letter_job_application", "010: added cover_letters.job_application_id column"),
        ("_011_add_resume_id_to_score_snapshots", "011: added score_snapshots.resume_id column"),
        ("_012_add_session_type_to_interview_sessions", "012: added interview_sessions.session_type columns"),
        ("_013_add_content_json_to_score_snapshots", "013: added score_snapshots.content_json column"),
        ("_014_add_conversation_status_override", "014: added job_applications.conversation_status_override column"),
        ("_015_add_activity_job_application", "015: added activity_events.related_job_application_id column"),
        ("_016_add_roadmap_task_statuses", "016: added roadmap_task_statuses table"),
        ("_017_add_cover_letter_generation_metadata", "017: added cover_letters generation metadata columns"),
        ("_018_add_insight_dismissals", "018: added insight_dismissals table"),
        ("_019_add_generation_method", "019: added communication_messages.generation_method column"),
    ]:
        migration = __import__(f"app.migrations.{module_name}", fromlist=["upgrade"])
        with engine.connect() as conn:
            added = migration.upgrade(conn)
            if added:
                conn.commit()
                import logging
                logging.getLogger(__name__).info(f"Applied migration {label} {added}")
