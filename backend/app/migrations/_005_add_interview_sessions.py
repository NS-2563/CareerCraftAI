"""Migration: Create interview_sessions table for persisted practice history.

Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS.
"""

from sqlalchemy import text, inspect


TABLE_NAME = "interview_sessions"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS interview_sessions (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    related_job_application_id INTEGER REFERENCES job_applications(id) ON DELETE SET NULL,
    job_title VARCHAR(255),
    skills TEXT,
    difficulty VARCHAR(50),
    question_count INTEGER NOT NULL DEFAULT 5,
    questions TEXT,
    answers TEXT,
    overall_score FLOAT,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

INDEX_SQL = "CREATE INDEX IF NOT EXISTS ix_interview_sessions_user_id ON interview_sessions(user_id)"


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade(conn):
    if not table_exists(conn, TABLE_NAME):
        conn.execute(text(CREATE_SQL))
        conn.execute(text(INDEX_SQL))
        return [TABLE_NAME]
    return []


def downgrade(conn):
    conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME}"))
