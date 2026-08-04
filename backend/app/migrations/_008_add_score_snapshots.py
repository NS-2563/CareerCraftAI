"""Migration: Create score_snapshots table for historical score tracking.

Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS.
"""

from sqlalchemy import text, inspect


TABLE_NAME = "score_snapshots"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS score_snapshots (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_type VARCHAR(64) NOT NULL,
    value FLOAT NOT NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

INDEX_USER_SQL = "CREATE INDEX IF NOT EXISTS ix_score_snapshots_user_id ON score_snapshots(user_id)"
INDEX_METRIC_SQL = "CREATE INDEX IF NOT EXISTS ix_score_snapshots_metric_type ON score_snapshots(metric_type)"


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade(conn):
    if not table_exists(conn, TABLE_NAME):
        conn.execute(text(CREATE_SQL))
        conn.execute(text(INDEX_USER_SQL))
        conn.execute(text(INDEX_METRIC_SQL))
        return [TABLE_NAME]
    return []


def downgrade(conn):
    conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME}"))
