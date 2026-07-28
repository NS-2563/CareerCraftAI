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

    Base.metadata.create_all(bind=engine)

    _run_pending_migrations()


def _run_pending_migrations():
    """Apply any schema changes that create_all() cannot handle (e.g., adding columns to existing tables)."""
    for module_name, label in [
        ("_003_add_missing_columns", "003: added columns"),
        ("_004_add_user_id_indexes", "004: added indexes"),
    ]:
        migration = __import__(f"app.migrations.{module_name}", fromlist=["upgrade"])
        with engine.connect() as conn:
            added = migration.upgrade(conn)
            if added:
                conn.commit()
                import logging
                logging.getLogger(__name__).info(f"Applied migration {label} {added}")
