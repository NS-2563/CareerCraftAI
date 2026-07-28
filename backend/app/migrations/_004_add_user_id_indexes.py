"""Migration: Add missing user_id indexes on tables that had index=False.

Missing indexes:
  resumes.user_id                → ix_resumes_user_id
  cover_letters.user_id          → ix_cover_letters_user_id
  communication_messages.user_id → ix_communication_messages_user_id
  communication_suggestions.user_id → ix_communication_suggestions_user_id

Safe to call multiple times — each CREATE INDEX uses IF NOT EXISTS.
"""

from sqlalchemy import text, inspect


INDEXES = [
    {"table": "resumes", "name": "ix_resumes_user_id", "sql": "CREATE INDEX IF NOT EXISTS ix_resumes_user_id ON resumes(user_id)"},
    {"table": "cover_letters", "name": "ix_cover_letters_user_id", "sql": "CREATE INDEX IF NOT EXISTS ix_cover_letters_user_id ON cover_letters(user_id)"},
    {"table": "communication_messages", "name": "ix_communication_messages_user_id", "sql": "CREATE INDEX IF NOT EXISTS ix_communication_messages_user_id ON communication_messages(user_id)"},
    {"table": "communication_suggestions", "name": "ix_communication_suggestions_user_id", "sql": "CREATE INDEX IF NOT EXISTS ix_communication_suggestions_user_id ON communication_suggestions(user_id)"},
]


def index_exists(conn, table_name: str, index_name: str) -> bool:
    """Check whether an index already exists in the given table."""
    inspector = inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade(conn):
    """Create all missing indexes."""
    added = []
    for entry in INDEXES:
        if not index_exists(conn, entry["table"], entry["name"]):
            conn.execute(text(entry["sql"]))
            added.append(f"{entry['table']}.{entry['name']}")
    return added


def downgrade(conn):
    """Drop all four user_id indexes."""
    for entry in INDEXES:
        conn.execute(text(f"DROP INDEX IF EXISTS {entry['name']}"))
