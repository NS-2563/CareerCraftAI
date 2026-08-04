"""Migration: Add session_type + real-interview log columns to interview_sessions.

Adds:
  interview_sessions.session_type            VARCHAR(50)   NOT NULL DEFAULT 'practice'
  interview_sessions.company_name            VARCHAR(255)  nullable
  interview_sessions.how_it_went             TEXT          nullable
  interview_sessions.self_rated_confidence   FLOAT         nullable
  interview_sessions.questions_asked         TEXT          nullable

Backfills every existing row to 'practice' (there were no real-interview logs
before this migration) and adds an index on session_type.

Safe to call multiple times — each ALTER is gated by a column-existence check.
"""

from sqlalchemy import text, inspect


TABLE = "interview_sessions"

COLUMNS = [
    ("session_type", "VARCHAR(50) NOT NULL DEFAULT 'practice'"),
    ("company_name", "VARCHAR(255)"),
    ("how_it_went", "TEXT"),
    ("self_rated_confidence", "FLOAT"),
    ("questions_asked", "TEXT"),
]


def column_exists(conn, table_name: str, column_name: str) -> bool:
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade(conn):
    if not table_exists(conn, TABLE):
        return []

    added = []
    for col_name, col_sql in COLUMNS:
        if not column_exists(conn, TABLE, col_name):
            conn.execute(text(
                f"ALTER TABLE {TABLE} ADD COLUMN {col_name} {col_sql}"
            ))
            added.append(f"{TABLE}.{col_name}")

    if f"{TABLE}.session_type" in added:
        conn.execute(text(
            "UPDATE interview_sessions "
            "SET session_type = 'practice' "
            "WHERE session_type IS NULL OR session_type = ''"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_interview_sessions_session_type "
            "ON interview_sessions (session_type)"
        ))

    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    pass
