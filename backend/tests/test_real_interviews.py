"""Tests for the real-interview logging feature.

Covers:
- Migration _012: ALTER + backfill to 'practice', column default, idempotency
- create_real_interview: requires an owned, existing job_application_id
- POST /api/interview-prep/real-interviews + list endpoint (ownership-scoped)
- list_sessions session_type filter and get_progress practice-only aggregation
- Career Coach context: real-interview block, weighting, isolation from practice
"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dependencies import create_access_token

# Import EVERY model so create_all resolves all foreign keys/relationships.
from app.models.user import User  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.career_report import CareerReport  # noqa: F401
from app.models.job_application import JobApplication  # noqa: F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: F401
from app.models.cover_letter import CoverLetter  # noqa: F401
from app.models.jd_match_result import JDMatchResult  # noqa: F401
from app.communication.models import CommunicationMessage, CommunicationSuggestion  # noqa: F401
from app.interview_prep.models import InterviewSession  # noqa: F401
from app.activity.models import ActivityEvent  # noqa: F401
from app.analytics.models import ScoreSnapshot  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    e = create_engine("sqlite://", connect_args={"check_same_thread": False})
    @event.listens_for(e, "connect")
    def _set_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=OFF;")
        cursor.close()

    Base.metadata.create_all(bind=e)
    return e


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, email="test@test.com", username="testuser", password="Test1234!"):
    from app.dependencies import get_password_hash
    u = User(email=email, username=username,
             hashed_password=get_password_hash(password), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_job(db, user_id, company="Acme", job_title="Engineer"):
    from app.schemas.job_tracker import JobStatus
    j = JobApplication(
        user_id=user_id, company=company, job_title=job_title,
        status=JobStatus("Applied"),
        job_description="Looking for a Python developer with FastAPI.",
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def _seed_real_interview(db, user_id, job, how_it_went="Went well overall",
                         confidence=75, questions="Tell me about yourself"):
    from app.interview_prep.service import InterviewPrepService
    from app.interview_prep.schemas import CreateRealInterviewRequest
    return InterviewPrepService.create_real_interview(
        db=db, user_id=user_id,
        request=CreateRealInterviewRequest(
            job_application_id=job.id,
            how_it_went=how_it_went,
            self_rated_confidence=confidence,
            questions_asked=questions,
        ),
    )


def _seed_practice(db, user_id, job_title="Practice Dev", score=60):
    from app.interview_prep.service import InterviewPrepService
    from app.interview_prep.schemas import CreateSessionRequest
    return InterviewPrepService.create_session(
        db=db, user_id=user_id,
        request=CreateSessionRequest(job_title=job_title, question_count=2),
    )


def _auth(user):
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Migration _012
# ---------------------------------------------------------------------------

OLD_SCHEMA = """
CREATE TABLE interview_sessions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    related_job_application_id INTEGER,
    job_title VARCHAR(255),
    job_role_normalized VARCHAR(255),
    skills TEXT,
    difficulty VARCHAR(50),
    question_count INTEGER NOT NULL DEFAULT 5,
    questions TEXT,
    answers TEXT,
    overall_score FLOAT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME NOT NULL
)
"""


class TestMigration012:

    def test_upgrade_adds_columns_and_backfills(self):
        from app.migrations._012_add_session_type_to_interview_sessions import (
            upgrade, column_exists, table_exists,
        )
        e = create_engine("sqlite://", connect_args={"check_same_thread": False})
        with e.begin() as conn:
            conn.execute(text(OLD_SCHEMA))
            conn.execute(text(
                "INSERT INTO interview_sessions (user_id, job_title, created_at) "
                "VALUES (1, 'Legacy Dev', '2024-01-01 00:00:00')"
            ))

        with e.begin() as conn:
            added = upgrade(conn)

        assert "interview_sessions.session_type" in added
        assert "interview_sessions.company_name" in added
        assert "interview_sessions.how_it_went" in added
        assert "interview_sessions.self_rated_confidence" in added
        assert "interview_sessions.questions_asked" in added

        with e.begin() as conn:
            assert column_exists(conn, "interview_sessions", "session_type")
            assert column_exists(conn, "interview_sessions", "company_name")
            assert column_exists(conn, "interview_sessions", "how_it_went")
            assert column_exists(conn, "interview_sessions", "self_rated_confidence")
            assert column_exists(conn, "interview_sessions", "questions_asked")

            # Existing rows backfilled to 'practice'.
            legacy = conn.execute(text(
                "SELECT session_type FROM interview_sessions WHERE id = 1"
            )).scalar()
            assert legacy == "practice"

            # New inserts get the 'practice' default without specifying it.
            conn.execute(text(
                "INSERT INTO interview_sessions (user_id, job_title, created_at) "
                "VALUES (2, 'New Dev', '2024-01-02 00:00:00')"
            ))
            new_row = conn.execute(text(
                "SELECT session_type FROM interview_sessions WHERE id = 2"
            )).scalar()
            assert new_row == "practice"

            # Index created.
            index_names = [ix["name"] for ix in
                           __import__("sqlalchemy").inspect(conn).get_indexes("interview_sessions")]
            assert "ix_interview_sessions_session_type" in index_names

            # Idempotent: second run adds nothing.
            added_again = upgrade(conn)
            assert added_again == []

    def test_upgrade_noop_when_table_missing(self):
        from app.migrations._012_add_session_type_to_interview_sessions import upgrade
        e = create_engine("sqlite://", connect_args={"check_same_thread": False})
        with e.begin() as conn:
            assert upgrade(conn) == []


# ---------------------------------------------------------------------------
# create_real_interview: ownership + snapshotting
# ---------------------------------------------------------------------------

class TestCreateRealInterviewService:

    def test_practice_session_gets_practice_type(self, db_session):
        user = _create_user(db_session)
        s = _seed_practice(db_session, user.id)
        assert s.session_type == "practice"
        assert s.overall_score is None

    def test_requires_owned_existing_job(self, db_session):
        from app.utils.exceptions import NotFoundException
        from app.interview_prep.service import InterviewPrepService
        from app.interview_prep.schemas import CreateRealInterviewRequest
        user = _create_user(db_session)

        with pytest.raises(NotFoundException):
            InterviewPrepService.create_real_interview(
                db=db_session, user_id=user.id,
                request=CreateRealInterviewRequest(
                    job_application_id=999999,
                    how_it_went="Good",
                    self_rated_confidence=70,
                ),
            )

        owner = _create_user(db_session, email="owner@test.com", username="owner")
        foreign_job = _create_job(db_session, owner.id, "OwnerCo")
        with pytest.raises(NotFoundException):
            InterviewPrepService.create_real_interview(
                db=db_session, user_id=user.id,
                request=CreateRealInterviewRequest(
                    job_application_id=foreign_job.id,
                    how_it_went="Good",
                    self_rated_confidence=70,
                ),
            )

    def test_snapshots_company_and_job_title(self, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id, "Acme Corp", "Backend Engineer")
        s = _seed_real_interview(db_session, user.id, job,
                                 how_it_went="Crushed it", confidence=90,
                                 questions="How do you handle conflict?")
        assert s.session_type == "real_interview"
        assert s.related_job_application_id == job.id
        assert s.company_name == "Acme Corp"
        assert s.job_title == "Backend Engineer"
        assert s.how_it_went == "Crushed it"
        assert s.self_rated_confidence == 90
        assert s.questions_asked == "How do you handle conflict?"
        assert s.overall_score is None
        assert s.completed_at is not None


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

class TestRealInterviewApi:

    @pytest.fixture
    def client(self, db_session):
        def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_create_real_interview(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id, "Acme Corp", "Engineer")
        headers = _auth(user)

        r = client.post("/api/interview-prep/real-interviews", headers=headers, json={
            "job_application_id": job.id,
            "how_it_went": "Tough but fair — two technical rounds.",
            "self_rated_confidence": 68,
            "questions_asked": "What is your approach to debugging?",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["session_type"] == "real_interview"
        assert data["related_job_application_id"] == job.id
        assert data["company_name"] == "Acme Corp"
        assert data["job_title"] == "Engineer"
        assert data["how_it_went"] == "Tough but fair — two technical rounds."
        assert data["self_rated_confidence"] == 68

    def test_create_requires_auth(self, client):
        r = client.post("/api/interview-prep/real-interviews", json={
            "job_application_id": 1,
            "how_it_went": "Good",
            "self_rated_confidence": 70,
        })
        assert r.status_code == 401

    def test_create_foreign_job_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job(db_session, owner.id, "OwnerCo")
        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = _auth(attacker)

        r = client.post("/api/interview-prep/real-interviews", headers=headers, json={
            "job_application_id": job.id,
            "how_it_went": "Good",
            "self_rated_confidence": 70,
        })
        assert r.status_code == 404

    def test_create_missing_job_returns_404(self, client, db_session):
        user = _create_user(db_session)
        headers = _auth(user)
        r = client.post("/api/interview-prep/real-interviews", headers=headers, json={
            "job_application_id": 999999,
            "how_it_went": "Good",
            "self_rated_confidence": 70,
        })
        assert r.status_code == 404

    def test_create_validation_errors(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        headers = _auth(user)
        base = {
            "job_application_id": job.id,
            "how_it_went": "Good",
            "self_rated_confidence": 70,
        }

        missing_how = dict(base)
        missing_how.pop("how_it_went")
        assert client.post("/api/interview-prep/real-interviews", headers=headers,
                           json=missing_how).status_code == 422

        missing_job = dict(base)
        missing_job.pop("job_application_id")
        assert client.post("/api/interview-prep/real-interviews", headers=headers,
                           json=missing_job).status_code == 422

        bad_confidence = dict(base)
        bad_confidence["self_rated_confidence"] = 150
        assert client.post("/api/interview-prep/real-interviews", headers=headers,
                           json=bad_confidence).status_code == 422

    def test_list_real_interviews_scoped_and_ordered(self, client, db_session):
        user = _create_user(db_session)
        job_a = _create_job(db_session, user.id, "Acme", "Engineer")
        job_b = _create_job(db_session, user.id, "Globex", "Analyst")
        _seed_real_interview(db_session, user.id, job_a, how_it_went="First")
        _seed_real_interview(db_session, user.id, job_a, how_it_went="Second")
        _seed_real_interview(db_session, user.id, job_b, how_it_went="Other job")
        _seed_practice(db_session, user.id)
        headers = _auth(user)

        r = client.get(f"/api/interview-prep/applications/{job_a.id}/real-interviews",
                       headers=headers)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert len(items) == 2
        assert [i["how_it_went"] for i in items] == ["Second", "First"]
        assert all(i["session_type"] == "real_interview" for i in items)

    def test_list_foreign_job_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job(db_session, owner.id)
        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = _auth(attacker)
        r = client.get(f"/api/interview-prep/applications/{job.id}/real-interviews",
                       headers=headers)
        assert r.status_code == 404

    def test_sessions_filter_by_session_type(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        _seed_practice(db_session, user.id, "Practice Dev")
        _seed_real_interview(db_session, user.id, job)
        headers = _auth(user)

        all_sessions = client.get("/api/interview-prep/sessions", headers=headers).json()
        assert all_sessions["data"]["pagination"]["total"] == 2

        practice = client.get("/api/interview-prep/sessions?session_type=practice",
                              headers=headers).json()
        assert practice["data"]["pagination"]["total"] == 1
        assert practice["data"]["items"][0]["session_type"] == "practice"

        real = client.get("/api/interview-prep/sessions?session_type=real_interview",
                          headers=headers).json()
        assert real["data"]["pagination"]["total"] == 1
        item = real["data"]["items"][0]
        assert item["session_type"] == "real_interview"
        assert item["self_rated_confidence"] == 75

        bad = client.get("/api/interview-prep/sessions?session_type=bogus",
                         headers=headers)
        assert bad.status_code == 422

    def test_progress_excludes_real_interviews(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        _seed_practice(db_session, user.id, "Practice Dev", score=60)
        _seed_real_interview(db_session, user.id, job)
        headers = _auth(user)

        r = client.get("/api/interview-prep/progress", headers=headers)
        assert r.status_code == 200
        assert r.json()["overview"]["total_sessions"] == 1


# ---------------------------------------------------------------------------
# Career Coach weighting
# ---------------------------------------------------------------------------

class TestCoachRealInterviewWeighting:

    def test_no_logs_fallback_line(self, db_session):
        user = _create_user(db_session)
        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={},
                            db=db_session, user_id=user.id)
        assert "- Real interviews: no real-interview logs yet (skipped)." in ctx
        assert "Real interview logs (from the user's own real interviews):" not in ctx

    def test_block_included_with_logs(self, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id, "Acme Corp", "Backend Engineer")
        _seed_real_interview(db_session, user.id, job,
                             how_it_went="System design round went well",
                             confidence=82, questions="Design a rate limiter.")

        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={},
                            db=db_session, user_id=user.id)
        assert "Real interview logs (from the user's own real interviews):" in ctx
        assert "real interview outcomes are MORE informative than practice scores" in ctx
        assert "Backend Engineer at Acme Corp" in ctx
        assert "self-rated confidence 82/100" in ctx
        assert "How it went: System design round went well" in ctx
        assert "Questions asked: Design a rate limiter." in ctx

    def test_practice_sessions_do_not_feed_the_block(self, db_session):
        user = _create_user(db_session)
        _seed_practice(db_session, user.id, "Practice Dev", score=60)

        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={},
                            db=db_session, user_id=user.id)
        assert "- Real interviews: no real-interview logs yet (skipped)." in ctx
        assert "Real interview logs (from the user's own real interviews):" not in ctx

    def test_real_logs_do_not_inflate_weakest_category(self, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        _seed_real_interview(db_session, user.id, job, how_it_went="Fine")

        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={},
                            db=db_session, user_id=user.id)
        # Practice-only aggregation -> a lone real-interview log never creates
        # a "weakest category" signal.
        assert "Weakest interview category" not in ctx
        assert "- Interview weaknesses: not enough practice data yet (skipped)." in ctx

    def test_block_limits_to_latest_five(self, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        for i in range(7):
            _seed_real_interview(db_session, user.id, job,
                                 how_it_went=f"Log {i}", confidence=50 + i)

        from app.ai.context_builder import _build_real_interview_block
        block = _build_real_interview_block(db_session, user.id)
        # 1 heading per log; each heading carries a "self-rated confidence" suffix.
        log_headings = [ln for ln in block if "self-rated confidence" in ln]
        assert len(log_headings) == 5

    def test_report_prompt_includes_weighting(self, db_session, monkeypatch):
        from app.interview_prep.models import InterviewSession
        user = _create_user(db_session)
        job = _create_job(db_session, user.id, "Acme Corp", "Engineer")
        _seed_real_interview(db_session, user.id, job, how_it_went="Strong systems round")

        captured = {}

        def fake_generate_json(prompt=None, schema=None):
            captured["prompt"] = prompt
            return {"success": True, "data": {
                "career_goal": "Engineer",
                "readiness_score": 70,
                "readiness_status": "Good",
                "best_match": "Engineer",
                "career_summary": "Solid.",
                "strengths": ["Python"],
                "weaknesses": ["Docker"],
                "career_paths": [],
                "skill_gap": {"existing_skills": ["Python"], "missing_skills": ["Docker"], "priority": ["Docker"]},
                "roadmap": [],
                "action_plan": {"next_week": [], "next_month": [], "next_6_months": []},
                "resources": [],
            }}

        monkeypatch.setattr(
            "app.career.services.roadmap_service.generate_json",
            fake_generate_json,
        )

        from app.career.services.roadmap_service import generate_career_report
        result = generate_career_report(
            {"goal": "Engineer", "skills": "Python"},
            db=db_session,
            user_id=user.id,
        )
        assert result.get("success") is True
        prompt = captured["prompt"]
        assert "Real interview logs" in prompt
        assert "Real interview logs (from the user's own real interviews):" in prompt
        assert "weight the real interview signal" in prompt
        assert "REAL USER SIGNALS" in prompt
        # A real-interview log exists in the DB but no interview session was
        # completed via update_session -> no interview_average snapshot.
        assert db_session.query(InterviewSession).count() == 1
