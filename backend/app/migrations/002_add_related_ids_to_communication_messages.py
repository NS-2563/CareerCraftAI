"""Migration: add related_job_application_id and related_resume_id to communication_messages.

Run strategy (example):
- Apply:
    ALTER TABLE communication_messages ADD COLUMN related_job_application_id INTEGER REFERENCES job_applications(id) ON DELETE SET NULL;
    ALTER TABLE communication_messages ADD COLUMN related_resume_id INTEGER REFERENCES resumes(id) ON DELETE SET NULL;
"""

from sqlalchemy import text


def upgrade(conn):
    conn.execute(text(
        "ALTER TABLE communication_messages ADD COLUMN related_job_application_id INTEGER REFERENCES job_applications(id) ON DELETE SET NULL"
    ))
    conn.execute(text(
        "ALTER TABLE communication_messages ADD COLUMN related_resume_id INTEGER REFERENCES resumes(id) ON DELETE SET NULL"
    ))


def downgrade(conn):
    return
