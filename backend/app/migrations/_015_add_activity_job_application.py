"""Migration: Add related_job_application_id to activity_events.

Adds:
  activity_events.related_job_application_id  INTEGER  nullable

Allows activity events produced by an application-linked module (communication
messages, cover letters, JD matches, interviews) to record the job application
they belong to, so the Activity Timeline can deep-link each entry back to the
application's workspace view. Nullable so pre-existing events behave exactly
as before. Safe to call multiple times; the ALTER is gated by a
column-existence check.
"""

from sqlalchemy import text, inspect


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check whether a column already exists in the given table."""
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(conn, table_name: str, index_name: str) -> bool:
    """Check whether an index already exists in the given table."""
    inspector = inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade(conn):
    """Add the related_job_application_id column + index if they do not exist."""
    added = []
    if not column_exists(conn, "activity_events", "related_job_application_id"):
        conn.execute(
            text("ALTER TABLE activity_events ADD COLUMN related_job_application_id INTEGER")
        )
        added.append("activity_events.related_job_application_id")
    if not index_exists(conn, "activity_events", "ix_activity_events_related_job_application_id"):
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_activity_events_related_job_application_id ON activity_events (related_job_application_id)")
        )
        added.append("activity_events.related_job_application_id index")
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
