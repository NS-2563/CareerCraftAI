"""Migration: Add missing columns to job_applications and communication_messages.

Missing columns identified by schema audit:
  job_applications.job_description       TEXT        nullable
  job_applications.resume_id             INTEGER     FK->resumes.id ON DELETE SET NULL, nullable
  communication_messages.related_job_application_id  INTEGER  FK->job_applications.id ON DELETE SET NULL, nullable
  communication_messages.related_resume_id           INTEGER  FK->resumes.id ON DELETE SET NULL, nullable

Safe to call multiple times — each ALTER TABLE is gated by a column-existence check.
"""

from sqlalchemy import text, inspect


MISSING_COLUMNS = [
    {"table": "job_applications", "column": "job_description", "sql": "ALTER TABLE job_applications ADD COLUMN job_description TEXT"},
    {"table": "job_applications", "column": "resume_id", "sql": "ALTER TABLE job_applications ADD COLUMN resume_id INTEGER REFERENCES resumes(id) ON DELETE SET NULL"},
    {"table": "communication_messages", "column": "related_job_application_id", "sql": "ALTER TABLE communication_messages ADD COLUMN related_job_application_id INTEGER REFERENCES job_applications(id) ON DELETE SET NULL"},
    {"table": "communication_messages", "column": "related_resume_id", "sql": "ALTER TABLE communication_messages ADD COLUMN related_resume_id INTEGER REFERENCES resumes(id) ON DELETE SET NULL"},
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
        if not column_exists(conn, entry["table"], entry["column"]):
            conn.execute(text(entry["sql"]))
            added.append(f"{entry['table']}.{entry['column']}")
    return added


def downgrade(conn):
    """SQLite cannot easily drop columns. Intentionally a no-op."""
    return
