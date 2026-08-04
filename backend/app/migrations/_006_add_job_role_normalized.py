"""Migration: Add job_role_normalized column to interview_sessions.

Backfills existing rows by deriving normalized value from job_title.

Safe to call multiple times — ALTER TABLE is gated by column-existence check.
"""

import re
from sqlalchemy import text, inspect


TABLE = "interview_sessions"
COLUMN = "job_role_normalized"


def _normalize(value):
    if not value or not value.strip():
        return None
    val = value.strip().lower()
    val = re.sub(r"\s+", " ", val)
    return val if val else None


def column_exists(conn, table_name: str, column_name: str) -> bool:
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade(conn):
    added = []
    if not column_exists(conn, TABLE, COLUMN):
        conn.execute(text(
            f"ALTER TABLE {TABLE} ADD COLUMN {COLUMN} VARCHAR(255)"
        ))
        added.append(f"{TABLE}.{COLUMN}")

        rows = conn.execute(text(f"SELECT id, job_title FROM {TABLE}")).fetchall()
        for row_id, job_title in rows:
            normalized = _normalize(job_title)
            if normalized:
                conn.execute(
                    text(f"UPDATE {TABLE} SET {COLUMN}=:val WHERE id=:id"),
                    {"val": normalized, "id": row_id},
                )

    return added


def downgrade(conn):
    pass
