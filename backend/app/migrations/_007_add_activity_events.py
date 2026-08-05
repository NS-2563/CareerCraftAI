"""Migration: Create activity_events table for cross-module activity log.

The table is expressed as a SQLAlchemy Core Table mirrored from the ORM model
(ActivityEvent), so the DDL is dialect-portable (auto-increment handled by each
dialect's own mechanism; no SQLite-only AUTOINCREMENT/DATETIME syntax).
Safe to call multiple times — guarded by a table-existence check and the
Core create uses checkfirst=True.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table, func, inspect

TABLE_NAME = "activity_events"

_META = MetaData()

# Parent table referenced by the user_id FK — lightweight stub so the DDL
# compiler can resolve "users". It is never created here; only the target
# table is created below, and the real parent already exists in the DB.
users = Table("users", _META, Column("id", Integer, primary_key=True))

TABLE = Table(
    TABLE_NAME,
    _META,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("event_type", String(64), nullable=False, index=True),
    Column("title", String(255), nullable=False),
    Column("description", String(500), nullable=True),
    Column("related_entity_type", String(64), nullable=True),
    Column("related_entity_id", Integer, nullable=True),
    Column("related_job_application_id", Integer, nullable=True, index=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
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
