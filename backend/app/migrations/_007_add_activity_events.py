"""Migration: Create activity_events table for cross-module activity log.

Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS.
"""

from sqlalchemy import text, inspect


TABLE_NAME = "activity_events"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS activity_events (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    related_entity_type VARCHAR(64),
    related_entity_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

INDEX_USER_SQL = "CREATE INDEX IF NOT EXISTS ix_activity_events_user_id ON activity_events(user_id)"
INDEX_TYPE_SQL = "CREATE INDEX IF NOT EXISTS ix_activity_events_event_type ON activity_events(event_type)"


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade(conn):
    if not table_exists(conn, TABLE_NAME):
        conn.execute(text(CREATE_SQL))
        conn.execute(text(INDEX_USER_SQL))
        conn.execute(text(INDEX_TYPE_SQL))
        return [TABLE_NAME]
    return []


def downgrade(conn):
    conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME}"))
