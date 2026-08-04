"""Migration: Add resume_id to score_snapshots.

Adds:
  score_snapshots.resume_id  INTEGER  nullable  FK -> resumes.id ON DELETE CASCADE

A score snapshot can now be tied to the specific resume it was computed for, so
each resume keeps its own ATS/resume score history. The column is nullable so
pre-existing user-level snapshots (career readiness, interview average, generic
ATS) are preserved. CASCADE deletes a snapshot when its resume is deleted — a
snapshot is meaningless without the resume it scored. Safe to call multiple
times; the ALTER is gated by a column-existence check.
"""

from sqlalchemy import text, inspect


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check whether a column already exists in the given table."""
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade(conn):
    """Add the resume_id column if it does not already exist."""
    added = []
    if not column_exists(conn, "score_snapshots", "resume_id"):
        conn.execute(
            text(
                "ALTER TABLE score_snapshots "
                "ADD COLUMN resume_id INTEGER "
                "REFERENCES resumes(id) ON DELETE CASCADE"
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_score_snapshots_resume_id "
                 "ON score_snapshots (resume_id)")
        )
        added.append("score_snapshots.resume_id")
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
