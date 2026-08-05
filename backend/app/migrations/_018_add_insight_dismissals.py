"""Migration: Create insight_dismissals table for workspace insight cards.

The table is expressed as a SQLAlchemy Core Table mirrored from the ORM model
(InsightDismissal), so the DDL is dialect-portable (auto-increment handled by
each dialect's own mechanism; no SQLite-only AUTOINCREMENT/DATETIME syntax).
Safe to call multiple times — guarded by a table-existence check and the
Core create uses checkfirst=True.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table, UniqueConstraint, func, inspect

TABLE_NAME = "insight_dismissals"

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
    Column("job_application_id", Integer, ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("insight_key", String(64), nullable=False, index=True),
    Column("dismissed_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    UniqueConstraint("user_id", "job_application_id", "insight_key", name="uq_insight_dismissal_user_job_key"),
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
