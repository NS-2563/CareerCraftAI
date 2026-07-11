"""Minimal migration for adding `completed` column to resumes.

This project currently appears to not use Alembic/Flask-Migrate migration tooling.
If a migration framework exists in your environment, wire this file accordingly.

Run strategy (example):
- Apply `ALTER TABLE resumes ADD COLUMN completed BOOLEAN NOT NULL DEFAULT 0;`

Note: SQLite uses 0/1 for booleans.
"""

from sqlalchemy import text


def upgrade(conn):
    conn.execute(text("ALTER TABLE resumes ADD COLUMN completed BOOLEAN NOT NULL DEFAULT 0"))


def downgrade(conn):
    # SQLite generally can't drop a column without table rebuild.
    # Intentionally left as no-op.
    return

