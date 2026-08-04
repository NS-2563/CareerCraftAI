"""Migration: Add generation metadata columns to cover_letters.

Adds:
  cover_letters.ai_provider    VARCHAR(50)   nullable
  cover_letters.model_name     VARCHAR(100)  nullable
  cover_letters.generated_at   DATETIME      nullable

Stores the real provider/model that produced a letter and the moment it was
generated. These are set server-side at AI generation time, never supplied by
the client, so the output view can show exactly what informed a letter. All
columns are nullable so pre-existing letters remain valid and simply show no
metadata. Safe to call multiple times; each ALTER is gated by a
column-existence check.
"""

from sqlalchemy import text, inspect


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check whether a column already exists in the given table."""
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade(conn):
    """Add the metadata columns if they do not already exist."""
    added = []
    if not column_exists(conn, "cover_letters", "ai_provider"):
        conn.execute(text("ALTER TABLE cover_letters ADD COLUMN ai_provider VARCHAR(50)"))
        added.append("cover_letters.ai_provider")
    if not column_exists(conn, "cover_letters", "model_name"):
        conn.execute(text("ALTER TABLE cover_letters ADD COLUMN model_name VARCHAR(100)"))
        added.append("cover_letters.model_name")
    if not column_exists(conn, "cover_letters", "generated_at"):
        conn.execute(text("ALTER TABLE cover_letters ADD COLUMN generated_at DATETIME"))
        added.append("cover_letters.generated_at")
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
