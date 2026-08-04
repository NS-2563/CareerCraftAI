"""Migration: Add content_json to score_snapshots.

Adds:
  score_snapshots.content_json  JSON  nullable

Stores a lightweight copy of the resume content (skills list + summary text) at
the moment the snapshot was recorded, so a later score-history diff can compare
actual content differences instead of guessing. The column is nullable so
pre-existing snapshots (recorded before content capture existed) remain valid
and are reported as "content not available" by the diff endpoint. Safe to call
multiple times; the ALTER is gated by a column-existence check.
"""

from sqlalchemy import text, inspect


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check whether a column already exists in the given table."""
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade(conn):
    """Add the content_json column if it does not already exist."""
    added = []
    if not column_exists(conn, "score_snapshots", "content_json"):
        conn.execute(
            text("ALTER TABLE score_snapshots ADD COLUMN content_json TEXT")
        )
        added.append("score_snapshots.content_json")
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
