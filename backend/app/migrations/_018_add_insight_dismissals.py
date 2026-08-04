"""Migration: Create insight_dismissals table for workspace insight cards.

Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS.
"""

from sqlalchemy import text, inspect


TABLE_NAME = "insight_dismissals"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS insight_dismissals (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_application_id INTEGER NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
    insight_key VARCHAR(64) NOT NULL,
    dismissed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_insight_dismissal_user_job_key UNIQUE (user_id, job_application_id, insight_key)
)
"""

INDEX_USER_SQL = "CREATE INDEX IF NOT EXISTS ix_insight_dismissals_user_id ON insight_dismissals(user_id)"
INDEX_JOB_SQL = "CREATE INDEX IF NOT EXISTS ix_insight_dismissals_job_application_id ON insight_dismissals(job_application_id)"
INDEX_KEY_SQL = "CREATE INDEX IF NOT EXISTS ix_insight_dismissals_insight_key ON insight_dismissals(insight_key)"


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade(conn):
    if not table_exists(conn, TABLE_NAME):
        conn.execute(text(CREATE_SQL))
        conn.execute(text(INDEX_USER_SQL))
        conn.execute(text(INDEX_JOB_SQL))
        conn.execute(text(INDEX_KEY_SQL))
        return [TABLE_NAME]
    return []


def downgrade(conn):
    conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME}"))
