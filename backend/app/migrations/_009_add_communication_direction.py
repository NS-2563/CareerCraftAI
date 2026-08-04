"""Migration: Add direction, sender_name, and sender_email to communication_messages.

Adds:
  communication_messages.direction       VARCHAR(10)  default 'outbound'  (inbound|outbound)
  communication_messages.sender_name     VARCHAR(255) nullable
  communication_messages.sender_email    VARCHAR(255) nullable

Backfills all existing rows as 'outbound' (every pre-existing message type was
implicitly outbound). Safe to call multiple times — each ALTER is gated by a
column-existence check.
"""

from sqlalchemy import text, inspect


MISSING_COLUMNS = [
    {"column": "direction", "sql": "ALTER TABLE communication_messages ADD COLUMN direction VARCHAR(10) NOT NULL DEFAULT 'outbound'"},
    {"column": "sender_name", "sql": "ALTER TABLE communication_messages ADD COLUMN sender_name VARCHAR(255)"},
    {"column": "sender_email", "sql": "ALTER TABLE communication_messages ADD COLUMN sender_email VARCHAR(255)"},
]


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check whether a column already exists in the given table."""
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade(conn):
    """Add all missing columns that don't already exist."""
    added = []
    for entry in MISSING_COLUMNS:
        if not column_exists(conn, "communication_messages", entry["column"]):
            conn.execute(text(entry["sql"]))
            added.append(f"communication_messages.{entry['column']}")

    # Backfill existing rows as outbound (idempotent).
    conn.execute(
        text("UPDATE communication_messages SET direction = 'outbound' WHERE direction IS NULL OR direction = ''")
    )
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
