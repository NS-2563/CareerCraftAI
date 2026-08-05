"""Migration: Create interview_sessions table for persisted practice history.

The table is expressed as a SQLAlchemy Core Table mirrored from the ORM model
(InterviewSession), so the DDL is dialect-portable (auto-increment handled by
each dialect's own mechanism; no SQLite-only AUTOINCREMENT/DATETIME syntax).
Safe to call multiple times — guarded by a table-existence check and the
Core create uses checkfirst=True.
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, MetaData, String, Table, Text, func, inspect

TABLE_NAME = "interview_sessions"

_META = MetaData()

# Parent tables referenced by FKs — lightweight stubs so the DDL compiler can
# resolve "users"/"job_applications". They are never created here; only the
# target table is created below, and the real parents already exist in the DB.
users = Table("users", _META, Column("id", Integer, primary_key=True))
job_applications = Table("job_applications", _META, Column("id", Integer, primary_key=True))

TABLE = Table(
    TABLE_NAME,
    _META,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("session_type", String(50), nullable=False, default="practice", index=True),
    Column("related_job_application_id", Integer, ForeignKey("job_applications.id", ondelete="SET NULL"), nullable=True),
    Column("job_title", String(255), nullable=True),
    Column("company_name", String(255), nullable=True),
    Column("job_role_normalized", String(255), nullable=True, index=True),
    Column("skills", Text, nullable=True),
    Column("difficulty", String(50), nullable=True),
    Column("question_count", Integer, nullable=False, default=5),
    Column("questions", Text, nullable=True),
    Column("answers", Text, nullable=True),
    Column("overall_score", Float, nullable=True),
    Column("how_it_went", Text, nullable=True),
    Column("self_rated_confidence", Float, nullable=True),
    Column("questions_asked", Text, nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade(conn):
    if not table_exists(conn, TABLE_NAME):
        TABLE.create(conn, checkfirst=True)
        return [TABLE_NAME]
    return []


def downgrade(conn):
    TABLE.drop(conn, checkfirst=True)
