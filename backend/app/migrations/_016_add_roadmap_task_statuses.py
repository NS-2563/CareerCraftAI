"""Migration: Create roadmap_task_statuses table for user-set recommendation status.

One row per user per recommendation (normalized skill name) so task statuses
persist independently of Career Coach report regeneration. The table is
expressed as a SQLAlchemy Core Table mirrored from the ORM model
(RoadmapTaskStatus), so the DDL is dialect-portable (auto-increment handled by
each dialect's own mechanism; no SQLite-only AUTOINCREMENT/DATETIME syntax).
Safe to call multiple times — guarded by a table-existence check and the
Core create uses checkfirst=True.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table, UniqueConstraint, func, inspect

TABLE_NAME = "roadmap_task_statuses"

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
    Column("skill", String(255), nullable=False, comment="Display casing of the recommendation skill"),
    Column("skill_key", String(255), nullable=False, comment="Lowercased/whitespace-normalized skill for identity matching"),
    Column("status", String(20), nullable=False, default="not_started"),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column("updated_at", DateTime, server_default=func.now(), nullable=False),
    UniqueConstraint("user_id", "skill_key", name="uq_roadmap_task_status_user_skill_key"),
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
