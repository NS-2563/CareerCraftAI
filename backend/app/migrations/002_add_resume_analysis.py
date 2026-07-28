"""
Migration 002: Add resume_analyses table.

Strategy:
- The project uses `Base.metadata.create_all()` in init_db(), so simply
  defining the ResumeAnalysis model and importing it in database.py is
  sufficient for new deployments.
- This script handles the case where the model exists but the table
  needs to be created manually (e.g., existing DB without auto-create).

Run:
    python -m app.migrations.002_add_resume_analysis
"""
import sys

from app.database import engine, Base
from app.models.resume_analysis import ResumeAnalysis


def upgrade():
    """Create resume_analyses table."""
    Base.metadata.create_all(bind=engine, tables=[ResumeAnalysis.__table__])
    print("Created resume_analyses table.")


def downgrade():
    """Drop resume_analyses table."""
    ResumeAnalysis.__table__.drop(bind=engine, checkfirst=True)
    print("Dropped resume_analyses table.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
