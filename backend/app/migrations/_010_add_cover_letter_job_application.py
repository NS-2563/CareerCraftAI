"""Migration: Add job_application_id to cover_letters.

Adds:
  cover_letters.job_application_id  INTEGER  nullable  FK -> job_applications.id ON DELETE SET NULL

A cover letter can now be linked to the application it was written for. The
link is nullable and uses SET NULL (not CASCADE) so deleting a job application
keeps the cover letter — it just becomes unlinked. Safe to call multiple times;
the ALTER is gated by a column-existence check.
"""

from sqlalchemy import text, inspect


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check whether a column already exists in the given table."""
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade(conn):
    """Add the job_application_id column if it does not already exist."""
    added = []
    if not column_exists(conn, "cover_letters", "job_application_id"):
        conn.execute(
            text(
                "ALTER TABLE cover_letters "
                "ADD COLUMN job_application_id INTEGER "
                "REFERENCES job_applications(id) ON DELETE SET NULL"
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_cover_letters_job_application_id "
                 "ON cover_letters (job_application_id)")
        )
        added.append("cover_letters.job_application_id")
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
