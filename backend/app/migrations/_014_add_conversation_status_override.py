"""Migration: Add conversation_status_override to job_applications.

Adds:
  job_applications.conversation_status_override  VARCHAR(20)  nullable

Holds the user's explicit conversation-status choice ("needs_reply", "waiting",
or "closed"). NULL means the status is derived automatically from the last
message's direction and the application's pipeline status. The column is
nullable so pre-existing applications behave exactly as before (auto/derived).
Safe to call multiple times; the ALTER is gated by a column-existence check.
"""

from sqlalchemy import text, inspect


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check whether a column already exists in the given table."""
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade(conn):
    """Add the conversation_status_override column if it does not already exist."""
    added = []
    if not column_exists(conn, "job_applications", "conversation_status_override"):
        conn.execute(
            text("ALTER TABLE job_applications ADD COLUMN conversation_status_override VARCHAR(20)")
        )
        added.append("job_applications.conversation_status_override")
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
