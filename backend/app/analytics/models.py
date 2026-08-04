from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from app.database import Base


class ScoreSnapshot(Base):
    __tablename__ = "score_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True, index=True)
    metric_type = Column(String(64), nullable=False, index=True)
    value = Column(Float, nullable=False)
    content_json = Column(
        JSON,
        nullable=True,
        comment="Lightweight resume content copy at snapshot time (skills + summary)",
    )
    recorded_at = Column(DateTime, default=func.now(), nullable=False)
