"""Migration: Add generation_method to communication_messages.

Adds:
  communication_messages.generation_method VARCHAR(20) NOT NULL DEFAULT 'manual'

Values: 'ai_generated' (created by the AI /generate endpoint) | 'manual'
(created by the manual create path or the manual log-inbound path).

Existing rows predate this column and cannot be reliably distinguished, so they
backfill as 'manual' — the conservative default. Safe to call multiple times;
the ALTER is gated by a column-existence check.
"""

from sqlalchemy import text, inspect


TABLE = "communication_messages"
COLUMN = "generation_method"


def column_exists(conn, table_name: str, column_name: str) -> bool:
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade(conn):
    added = []
    if not column_exists(conn, TABLE, COLUMN):
        conn.execute(
            text(
                f"ALTER TABLE {TABLE} ADD COLUMN {COLUMN} VARCHAR(20) "
                "NOT NULL DEFAULT 'manual'"
            )
        )
        added.append(f"{TABLE}.{COLUMN}")
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
