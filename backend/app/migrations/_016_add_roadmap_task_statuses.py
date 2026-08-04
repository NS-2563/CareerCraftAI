"""Migration: Create roadmap_task_statuses table for user-set recommendation status.

One row per user per recommendation (normalized skill name) so task statuses
persist independently of Career Coach report regeneration. Safe to call
multiple times — uses CREATE TABLE IF NOT EXISTS.
"""

from sqlalchemy import text, inspect


TABLE_NAME = "roadmap_task_statuses"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS roadmap_task_statuses (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill VARCHAR(255) NOT NULL,
    skill_key VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

INDEX_USER_SQL = "CREATE INDEX IF NOT EXISTS ix_roadmap_task_statuses_user_id ON roadmap_task_statuses(user_id)"
UNIQUE_SKILL_SQL = (
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_roadmap_task_status_user_skill_key "
    "ON roadmap_task_statuses(user_id, skill_key)"
)


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade(conn):
    if not table_exists(conn, TABLE_NAME):
        conn.execute(text(CREATE_SQL))
        conn.execute(text(INDEX_USER_SQL))
        conn.execute(text(UNIQUE_SKILL_SQL))
        return [TABLE_NAME]
    return []


def downgrade(conn):
    conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME}"))
