"""Migration: Create score_snapshots table for historical score tracking.

The table is expressed as a SQLAlchemy Core Table mirrored from the ORM model
(ScoreSnapshot), so the DDL is dialect-portable (auto-increment handled by each
dialect's own mechanism; no SQLite-only AUTOINCREMENT/DATETIME syntax).
Safe to call multiple times — guarded by a table-existence check and the
Core create uses checkfirst=True.
"""

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, MetaData, String, Table, func, inspect

TABLE_NAME = "score_snapshots"

_META = MetaData()

# Parent tables referenced by FKs — lightweight stubs so the DDL compiler can
# resolve "users"/"resumes". They are never created here; only the target
# table is created below, and the real parents already exist in the DB.
users = Table("users", _META, Column("id", Integer, primary_key=True))
resumes = Table("resumes", _META, Column("id", Integer, primary_key=True))

TABLE = Table(
    TABLE_NAME,
    _META,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("resume_id", Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True, index=True),
    Column("metric_type", String(64), nullable=False, index=True),
    Column("value", Float, nullable=False),
    Column("content_json", JSON, nullable=True, comment="Lightweight resume content copy at snapshot time (skills + summary)"),
    Column("recorded_at", DateTime, default=func.now(), nullable=False),
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
