"""Tests for interview progress aggregation and job_role normalization."""

import json
import pytest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
# Import EVERY model so create_all resolves all foreign keys
from app.models.user import User  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.career_report import CareerReport  # noqa: F401
from app.models.job_application import JobApplication  # noqa: F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: F401
from app.models.cover_letter import CoverLetter  # noqa: F401
from app.communication.models import CommunicationMessage, CommunicationSuggestion  # noqa: F401
from app.interview_prep.models import InterviewSession  # noqa: F401

from app.interview_prep.service import normalize_job_role, InterviewPrepService

TEST_DB_URL = "sqlite:///:memory:"
_test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=_test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_session(db, user_id, job_title, overall_score, answers=None, created_offset_hours=0, questions=None):
    """Helper to create test sessions with arbitrary dates."""
    sess = InterviewSession(
        user_id=user_id,
        job_title=job_title,
        job_role_normalized=normalize_job_role(job_title),
        overall_score=overall_score,
        question_count=5,
        questions=json.dumps(questions or [
            {"id": "q1", "question": "Test?", "category": "Technical", "difficulty": "medium"},
            {"id": "q2", "question": "Test2?", "category": "Behavioral", "difficulty": "easy"},
        ]),
        answers=json.dumps(answers or []),
        created_at=datetime.utcnow() - timedelta(hours=created_offset_hours),
        started_at=datetime.utcnow() - timedelta(hours=created_offset_hours),
        completed_at=datetime.utcnow() if overall_score is not None else None,
    )
    db.add(sess)
    db.commit()
    return sess


class TestNormalizeJobRole:
    def test_trims_whitespace(self):
        assert normalize_job_role("  Backend Developer  ") == "backend developer"

    def test_lowercases(self):
        assert normalize_job_role("Backend Developer") == "backend developer"

    def test_collapses_internal_whitespace(self):
        assert normalize_job_role("Backend   Developer") == "backend developer"

    def test_mixed_case_and_whitespace(self):
        assert normalize_job_role("  Senior   BACKEND Engineer  ") == "senior backend engineer"

    def test_empty_returns_none(self):
        assert normalize_job_role("") is None

    def test_none_returns_none(self):
        assert normalize_job_role(None) is None

    def test_whitespace_only_returns_none(self):
        assert normalize_job_role("   ") is None


class TestTrendCalculation:
    def test_not_enough_data_with_few_sessions(self, db_session):
        uid = 99901
        for i in range(3):
            _make_session(db_session, uid, "Dev", 50.0, created_offset_hours=i)
        result = InterviewPrepService.get_progress(db_session, uid)
        assert result.overview.trend == "not_enough_data"
        assert result.overview.total_sessions == 3
        assert result.overview.average_score == 50.0

    def test_not_enough_data_with_zero_sessions(self, db_session):
        uid = 99902
        result = InterviewPrepService.get_progress(db_session, uid)
        assert result.overview.trend == "not_enough_data"
        assert result.overview.total_sessions == 0
        assert result.overview.average_score is None

    def test_improving_trend(self, db_session):
        uid = 99903
        # oldest sessions (high offset) have low scores, newest (low offset) have high scores
        scores = [65, 60, 55, 50, 45, 40, 35, 30]
        for i, s in enumerate(scores):
            _make_session(db_session, uid, "Dev", float(s), created_offset_hours=i)
        result = InterviewPrepService.get_progress(db_session, uid)
        assert result.overview.trend == "improving"

    def test_declining_trend(self, db_session):
        uid = 99904
        # oldest sessions have high scores, newest have low scores
        scores = [45, 50, 55, 60, 65, 70, 75, 80]
        for i, s in enumerate(scores):
            _make_session(db_session, uid, "Dev", float(s), created_offset_hours=i)
        result = InterviewPrepService.get_progress(db_session, uid)
        assert result.overview.trend == "declining"

    def test_flat_trend(self, db_session):
        uid = 99905
        scores = [55, 56, 54, 55, 56, 55, 54, 56]
        for i, s in enumerate(scores):
            _make_session(db_session, uid, "Dev", float(s), created_offset_hours=i)
        result = InterviewPrepService.get_progress(db_session, uid)
        assert result.overview.trend == "flat"


class TestRoleGrouping:
    def test_different_casing_groups_together(self, db_session):
        uid = 99906
        _make_session(db_session, uid, "Backend Developer", 70.0, created_offset_hours=0)
        _make_session(db_session, uid, "backend developer ", 80.0, created_offset_hours=1)
        result = InterviewPrepService.get_progress(db_session, uid)
        assert len(result.by_role) == 1
        assert result.by_role[0].job_role_normalized == "backend developer"
        assert result.by_role[0].session_count == 2

    def test_different_roles_separate(self, db_session):
        uid = 99907
        _make_session(db_session, uid, "Frontend Dev", 70.0, created_offset_hours=0)
        _make_session(db_session, uid, "Backend Dev", 80.0, created_offset_hours=1)
        result = InterviewPrepService.get_progress(db_session, uid)
        assert len(result.by_role) == 2


class TestSortParam:
    def test_score_asc_default(self, db_session):
        uid = 99908
        _make_session(db_session, uid, "AAA Role", 90.0, created_offset_hours=0)
        _make_session(db_session, uid, "BBB Role", 50.0, created_offset_hours=1)
        result = InterviewPrepService.get_progress(db_session, uid, sort="score_asc")
        assert result.by_role[0].average_score == 50.0
        assert result.by_role[1].average_score == 90.0

    def test_score_desc(self, db_session):
        uid = 99909
        _make_session(db_session, uid, "AAA Role", 50.0, created_offset_hours=0)
        _make_session(db_session, uid, "BBB Role", 90.0, created_offset_hours=1)
        result = InterviewPrepService.get_progress(db_session, uid, sort="score_desc")
        assert result.by_role[0].average_score == 90.0
        assert result.by_role[1].average_score == 50.0

    def test_session_count_sort(self, db_session):
        uid = 99910
        _make_session(db_session, uid, "Many Role", 70.0, created_offset_hours=0)
        _make_session(db_session, uid, "Many Role", 75.0, created_offset_hours=1)
        _make_session(db_session, uid, "Few Role", 80.0, created_offset_hours=2)
        result = InterviewPrepService.get_progress(db_session, uid, sort="session_count")
        assert result.by_role[0].session_count == 2
        assert result.by_role[1].session_count == 1


class TestByCategory:
    def test_aggregates_categories_from_questions(self, db_session):
        uid = 99911
        questions = [
            {"id": "q1", "question": "Tech Q?", "category": "Technical", "difficulty": "medium"},
            {"id": "q2", "question": "Behav Q?", "category": "Behavioral", "difficulty": "medium"},
        ]
        answers = [
            {"questionId": "q1", "answer": "My answer", "skipped": False, "evaluation": {"score": 80, "evaluation_failed": False}},
            {"questionId": "q2", "answer": "My answer", "skipped": False, "evaluation": {"score": 60, "evaluation_failed": False}},
        ]
        _make_session(db_session, uid, "Dev", 70.0, answers=answers, questions=questions, created_offset_hours=0)
        result = InterviewPrepService.get_progress(db_session, uid)
        cats = {c.category: c for c in result.by_category}
        assert "Technical" in cats
        assert "Behavioral" in cats
        assert cats["Technical"].average_score == 80.0
        assert cats["Behavioral"].average_score == 60.0
