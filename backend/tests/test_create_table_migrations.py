"""Tests for the dialect-portable CREATE TABLE migrations.

The five table-creation migrations previously carried hand-written SQLite-only
DDL (AUTOINCREMENT, DATETIME) that only ever worked because
``Base.metadata.create_all()`` happened to create the same tables first (a
coincidence of import ordering, not a guarantee). These tests prove the
replacement SQLAlchemy Core DDL:

1. Actually executes (not skipped) when the table does NOT pre-exist.
2. Is faithful to the ORM model (identical compiled DDL on both dialects).
3. Is valid dialect-portable DDL (no AUTOINCREMENT/DATETIME; SERIAL on PG).
4. Remains compatible with the later column-adding migrations (which must no-op).
"""

import os
import re
import tempfile

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

import app.main  # noqa: F401  — registers every model on Base.metadata
from app.database import Base
from app.migrations import (
    _005_add_interview_sessions,
    _006_add_job_role_normalized,
    _007_add_activity_events,
    _008_add_score_snapshots,
    _011_add_resume_id_to_score_snapshots,
    _012_add_session_type_to_interview_sessions,
    _013_add_content_json_to_score_snapshots,
    _015_add_activity_job_application,
    _016_add_roadmap_task_statuses,
    _018_add_insight_dismissals,
)
from app.activity.models import ActivityEvent
from app.analytics.models import ScoreSnapshot
from app.interview_prep.models import InterviewSession
from app.models.insight_dismissal import InsightDismissal
from app.models.job_application import JobApplication
from app.models.resume import Resume
from app.models.roadmap_task_status import RoadmapTaskStatus
from app.models.user import User


CREATE_MIGRATIONS = [
    _005_add_interview_sessions,
    _007_add_activity_events,
    _008_add_score_snapshots,
    _016_add_roadmap_task_statuses,
    _018_add_insight_dismissals,
]

# Later ALTER migrations that add columns/indexes to these tables. Every one is
# gated by column/index-existence checks and must no-op once the create
# migrations have produced the full ORM schema.
LATER_ALTERS = [
    _006_add_job_role_normalized,
    _011_add_resume_id_to_score_snapshots,
    _012_add_session_type_to_interview_sessions,
    _013_add_content_json_to_score_snapshots,
    _015_add_activity_job_application,
]

MODELS = {
    "interview_sessions": InterviewSession,
    "activity_events": ActivityEvent,
    "score_snapshots": ScoreSnapshot,
    "roadmap_task_statuses": RoadmapTaskStatus,
    "insight_dismissals": InsightDismissal,
}


def _fresh_engine():
    """A fresh, file-backed SQLite engine (in-memory would not persist across
    separate engine.connect() calls the way the migrations use them)."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return create_engine(f"sqlite:///{path}"), path


def _drop_target_tables(engine):
    with engine.begin() as conn:
        for mig in CREATE_MIGRATIONS:
            conn.execute(text(f'DROP TABLE IF EXISTS "{mig.TABLE_NAME}"'))


class TestCreateTableMigrationsExecuteWhenAbsent:

    def test_upgrade_creates_each_table_when_missing(self):
        engine, path = _fresh_engine()
        try:
            with engine.begin() as conn:
                Base.metadata.create_all(conn)  # parents + the five targets
            _drop_target_tables(engine)  # force the migrations to do the work

            for mig in CREATE_MIGRATIONS:
                with engine.begin() as conn:
                    added = mig.upgrade(conn)
                assert added == [mig.TABLE_NAME], (
                    f"{mig.TABLE_NAME} upgrade() did not actually create the table"
                )

            inspector = inspect(engine)
            for mig in CREATE_MIGRATIONS:
                assert mig.TABLE_NAME in inspector.get_table_names()
        finally:
            engine.dispose()
            os.unlink(path)

    def test_upgrade_is_idempotent_when_table_already_exists(self):
        engine, path = _fresh_engine()
        try:
            with engine.begin() as conn:
                Base.metadata.create_all(conn)
            for mig in CREATE_MIGRATIONS:
                with engine.begin() as conn:
                    assert mig.upgrade(conn) == [], (
                        f"{mig.TABLE_NAME} should be skipped when it exists"
                    )
        finally:
            engine.dispose()
            os.unlink(path)

    def test_later_alter_migrations_noop_after_create_migrations(self):
        """The create migrations produce the full ORM schema, so every later
        gated ALTER migration must report nothing added."""
        engine, path = _fresh_engine()
        try:
            with engine.begin() as conn:
                Base.metadata.create_all(conn)
            _drop_target_tables(engine)

            for mig in CREATE_MIGRATIONS:
                with engine.begin() as conn:
                    mig.upgrade(conn)

            for mig in LATER_ALTERS:
                with engine.begin() as conn:
                    assert mig.upgrade(conn) == [], (
                        f"{mig.__name__} should no-op after the create migrations"
                    )
        finally:
            engine.dispose()
            os.unlink(path)

    def test_orm_models_work_against_migrated_tables(self):
        """End-to-end: create the parents, drop the five targets, run the five
        migrations, then persist + read rows through the ORM models."""
        engine, path = _fresh_engine()
        try:
            with engine.begin() as conn:
                Base.metadata.create_all(conn)
            _drop_target_tables(engine)
            for mig in CREATE_MIGRATIONS:
                with engine.begin() as conn:
                    mig.upgrade(conn)

            with Session(engine) as session:
                user = User(email="u@example.com", username="u", hashed_password="x")
                session.add(user)
                session.flush()

                job = JobApplication(user_id=user.id, company="Acme", job_title="Dev")
                resume = Resume(user_id=user.id)
                session.add_all([job, resume])
                session.flush()

                session.add_all([
                    InterviewSession(user_id=user.id),
                    ActivityEvent(user_id=user.id, event_type="test", title="t"),
                    ScoreSnapshot(user_id=user.id, metric_type="ats", value=50.0),
                    RoadmapTaskStatus(user_id=user.id, skill="Python", skill_key="python"),
                    InsightDismissal(user_id=user.id, job_application_id=job.id, insight_key="k"),
                ])
                session.commit()

                assert session.query(InterviewSession).filter_by(user_id=user.id).count() == 1
                assert session.query(ActivityEvent).filter_by(user_id=user.id).count() == 1
                assert session.query(ScoreSnapshot).filter_by(user_id=user.id).count() == 1
                assert session.query(RoadmapTaskStatus).filter_by(user_id=user.id).count() == 1
                assert session.query(InsightDismissal).filter_by(user_id=user.id).count() == 1
        finally:
            engine.dispose()
            os.unlink(path)


def _normalize(ddl: str) -> str:
    return re.sub(r"\s+", " ", ddl).strip()


class TestFullMigrationChainWithTablesAbsent:

    def test_run_pending_migrations_recreates_dropped_tables(self, monkeypatch):
        """The real startup path — init_db()'s _run_pending_migrations() — must
        rebuild these tables from the migration DDL when create_all() did not
        leave them behind."""
        import app.database as database_mod

        engine, path = _fresh_engine()
        try:
            with engine.begin() as conn:
                Base.metadata.create_all(conn)
            _drop_target_tables(engine)

            monkeypatch.setattr(database_mod, "engine", engine)
            database_mod._run_pending_migrations()

            inspector = inspect(engine)
            for mig in CREATE_MIGRATIONS:
                assert mig.TABLE_NAME in inspector.get_table_names(), (
                    f"{mig.TABLE_NAME} missing after the full migration chain"
                )
        finally:
            engine.dispose()
            os.unlink(path)


class TestDialectPortability:

    def test_postgres_ddl_has_no_sqlite_only_syntax(self):
        pg = postgresql.dialect()
        for mig in CREATE_MIGRATIONS:
            ddl = str(CreateTable(mig.TABLE).compile(dialect=pg)).upper()
            assert "AUTOINCREMENT" not in ddl, mig.TABLE_NAME
            assert "DATETIME" not in ddl, mig.TABLE_NAME
            assert "SERIAL" in ddl, f"{mig.TABLE_NAME} PK should render as SERIAL on PG"

    def test_sqlite_ddl_has_no_sqlite_only_syntax(self):
        sl = sqlite.dialect()
        for mig in CREATE_MIGRATIONS:
            ddl = str(CreateTable(mig.TABLE).compile(dialect=sl)).upper()
            # AUTOINCREMENT is the SQLite-only piece of the old raw SQL. DATETIME
            # is legitimately rendered by SQLAlchemy on SQLite (native type) and
            # is ported correctly by the dialect, so it is not checked here.
            assert "AUTOINCREMENT" not in ddl, mig.TABLE_NAME

    @pytest.mark.parametrize("dialect", [sqlite.dialect(), postgresql.dialect()])
    def test_migration_ddl_matches_orm_model(self, dialect):
        for mig in CREATE_MIGRATIONS:
            model_ddl = _normalize(str(CreateTable(MODELS[mig.TABLE_NAME].__table__).compile(dialect=dialect)))
            mig_ddl = _normalize(str(CreateTable(mig.TABLE).compile(dialect=dialect)))
            assert mig_ddl == model_ddl, (
                f"{mig.TABLE_NAME} DDL diverged from the ORM model for {dialect.name}"
            )
