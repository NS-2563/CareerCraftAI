"""Tests for the Dashboard summary endpoint and service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dashboard.service import DashboardService
from app.analytics.service import AnalyticsService


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
    from app.models.user import User
    u = User(email=email, username=username,
             hashed_password=get_password_hash(password), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_resume(db, user_id, name="Test Resume", completed=True, archived=False):
    from app.models.resume import Resume
    r = Resume(user_id=user_id, name=name, completed=completed, is_archived=archived)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _create_job_application(db, user_id, company="Acme", job_title="Engineer", status="Applied"):
    from app.models.job_application import JobApplication
    from app.schemas.job_tracker import JobStatus
    j = JobApplication(
        user_id=user_id, company=company, job_title=job_title,
        status=JobStatus(status) if isinstance(status, str) else status,
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def _create_interview_session(db, user_id, job_title="Engineer", overall_score=None):
    from datetime import datetime, timezone
    from app.interview_prep.models import InterviewSession
    completed = datetime.now(timezone.utc).replace(tzinfo=None) if overall_score is not None else None
    s = InterviewSession(
        user_id=user_id, job_title=job_title, difficulty="medium",
        question_count=5, overall_score=overall_score,
        completed_at=completed,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _create_career_report(db, user_id, readiness_score=70):
    from app.models.career_report import CareerReport
    cr = CareerReport(user_id=user_id, career_goal="Software Engineer",
                      readiness_score=readiness_score,
                      source="ai", report_json={})
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return cr


def _create_activity_event(db, user_id, event_type="resume_created", title="Test"):
    from app.activity.models import ActivityEvent
    from app.activity.constants import EventType
    if isinstance(event_type, str):
        event_type = event_type
    ev = ActivityEvent(user_id=user_id, event_type=event_type, title=title)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def _create_cover_letter(db, user_id, title="CL"):
    from app.models.cover_letter import CoverLetter
    cl = CoverLetter(user_id=user_id, title=title)
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl


def _create_communication_message(db, user_id, subject="Msg"):
    from app.communication.models import CommunicationMessage
    msg = CommunicationMessage(user_id=user_id, message_type="follow_up",
                                recipient_name="Recipient", subject=subject,
                                body="Test message body")
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# ---------------------------------------------------------------------------
# Unit: DashboardService
# ---------------------------------------------------------------------------

class TestDashboardService:

    def test_full_user(self, db_session):
        user = _create_user(db_session)
        _create_resume(db_session, user.id, "Resume A", completed=True)
        _create_resume(db_session, user.id, "Resume B", completed=False)
        _create_job_application(db_session, user.id, "Acme", "Engineer", "Applied")
        _create_job_application(db_session, user.id, "Google", "SWE", "Interview")
        _create_interview_session(db_session, user.id, "SWE", overall_score=80.0)
        _create_career_report(db_session, user.id, readiness_score=75)
        _create_activity_event(db_session, user.id, "resume_created", "Created resume")
        _create_cover_letter(db_session, user.id)
        _create_communication_message(db_session, user.id)

        summary = DashboardService.get_summary(db_session, user.id)

        assert not summary["is_empty"]
        assert summary["resume"]["count"] == 2
        assert summary["resume"]["has_completed"] is True
        assert summary["resume"]["created_this_week"] == 2
        assert summary["job_stats"]["total_applications"] == 2
        assert summary["job_stats"]["interview_count"] == 1
        assert summary["interview"]["total_sessions"] == 1
        assert summary["interview"]["average_score"] == 80.0
        assert summary["career_readiness"]["score"] == 75
        assert summary["career_readiness"]["last_updated"] is not None
        assert len(summary["recent_activity"]) == 1
        assert len(summary["continue_items"]) >= 1
        assert len(summary["career_journey"]) == 6
        assert len(summary["ai_insights"]) >= 1

    def test_resume_created_this_week_excludes_old_resumes(self, db_session):
        from datetime import datetime, timedelta, timezone
        from app.models.resume import Resume

        user = _create_user(db_session)
        _create_resume(db_session, user.id, "New Resume", completed=True)

        old = _create_resume(db_session, user.id, "Old Resume", completed=True)
        old.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=20)
        db_session.commit()

        summary = DashboardService.get_summary(db_session, user.id)

        assert summary["resume"]["count"] == 2
        assert summary["resume"]["created_this_week"] == 1

    def test_career_readiness_last_updated_absent_when_no_report(self, db_session):
        user = _create_user(db_session)
        summary = DashboardService.get_summary(db_session, user.id)

        assert summary["career_readiness"] is None

    def test_brand_new_user(self, db_session):
        user = _create_user(db_session)
        summary = DashboardService.get_summary(db_session, user.id)

        assert summary["is_empty"] is True
        assert summary["resume"]["count"] == 0
        assert all(s["status"] == "not_started" for s in summary["career_journey"])
        assert len(summary["career_journey"]) == 6
        assert summary["recent_activity"] == []
        assert summary["ai_insights"] == []
        assert summary["continue_items"] == {}

    def test_partial_user_no_interview(self, db_session):
        user = _create_user(db_session)
        _create_resume(db_session, user.id, "My Resume", completed=True)
        _create_job_application(db_session, user.id, "Acme", "Engineer", "Applied")

        summary = DashboardService.get_summary(db_session, user.id)

        assert not summary["is_empty"]
        assert summary["resume"]["count"] == 1
        assert summary["job_stats"]["total_applications"] == 1
        assert summary["interview"]["total_sessions"] == 0
        assert summary["interview"]["average_score"] is None
        assert summary["interview"]["latest_session"] is None
        assert summary["career_readiness"] is None

    def test_resume_section_fails_gracefully(self, db_session):
        user = _create_user(db_session)
        summary = DashboardService.get_summary(db_session, user.id)
        assert "resume" in summary

    def test_career_journey_states(self, db_session):
        user = _create_user(db_session)
        _create_resume(db_session, user.id, "R1", completed=True)
        _create_job_application(db_session, user.id)
        _create_interview_session(db_session, user.id, overall_score=90.0)

        summary = DashboardService.get_summary(db_session, user.id)
        stages = {s["id"]: s["status"] for s in summary["career_journey"]}

        assert stages["resume"] == "complete"
        assert stages["analysis"] == "not_started"
        assert stages["career_coach"] == "not_started"
        assert stages["job_applications"] == "complete"
        assert stages["interview_prep"] == "complete"
        assert stages["communication"] == "not_started"

    def test_ats_insight_only_with_two_snapshots(self, db_session):
        user = _create_user(db_session)
        AnalyticsService.record_snapshot(db_session, user.id, "ats_score", 70.0)

        summary = DashboardService.get_summary(db_session, user.id)
        ats_insights = [i for i in summary["ai_insights"] if i["type"] == "ats_trend"]
        assert len(ats_insights) == 0

        AnalyticsService.record_snapshot(db_session, user.id, "ats_score", 80.0)
        summary = DashboardService.get_summary(db_session, user.id)
        ats_insights = [i for i in summary["ai_insights"] if i["type"] == "ats_trend"]
        assert len(ats_insights) == 1
        assert "improved" in ats_insights[0]["message"]

    def test_follow_up_insight_from_suggestions(self, db_session):
        from app.communication.models import CommunicationSuggestion
        from app.models.job_application import JobApplication
        from app.schemas.job_tracker import JobStatus

        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id, "Google", "SWE", "Applied")

        sug = CommunicationSuggestion(
            user_id=user.id, job_application_id=job.id,
            suggestion_type="follow_up_due", is_dismissed=False,
        )
        db_session.add(sug)
        db_session.commit()

        summary = DashboardService.get_summary(db_session, user.id)
        follow_ups = [i for i in summary["ai_insights"] if i["type"] == "follow_up"]
        assert len(follow_ups) >= 1
        assert "Google" in follow_ups[0]["message"]


# ---------------------------------------------------------------------------
# API: GET /api/dashboard/summary
# ---------------------------------------------------------------------------

class TestDashboardApi:

    @pytest.fixture
    def client(self, db_session):
        def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def test_user(self, db_session, client):
        user = _create_user(db_session)
        r = client.post("/api/auth/login", json={
            "email": "test@test.com", "password": "Test1234!",
        })
        assert r.status_code == 200
        token = r.json().get("access_token", "")
        return user, {"Authorization": f"Bearer {token}"}

    def test_requires_auth(self, client):
        r = client.get("/api/dashboard/summary")
        assert r.status_code == 401

    def test_empty_user(self, client, test_user):
        _, headers = test_user
        r = client.get("/api/dashboard/summary", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["is_empty"] is True
        assert data["data"]["resume"]["count"] == 0

    def test_populated_user(self, client, test_user, db_session):
        user, headers = test_user
        _create_resume(db_session, user.id, "Full User Resume", completed=True)
        _create_job_application(db_session, user.id, "Corp", "Dev", "Interview")
        _create_interview_session(db_session, user.id, "Dev", overall_score=85.0)
        _create_career_report(db_session, user.id, readiness_score=80)
        _create_activity_event(db_session, user.id, "resume_created", "Created")

        r = client.get("/api/dashboard/summary", headers=headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert not data["is_empty"]
        assert data["resume"]["count"] == 1
        assert data["job_stats"]["total_applications"] == 1
        assert data["job_stats"]["interview_count"] == 1
        assert data["interview"]["total_sessions"] == 1
        assert data["career_readiness"]["score"] == 80
        assert len(data["recent_activity"]) == 1
        assert len(data["career_journey"]) == 6

    def test_partial_user(self, client, test_user, db_session):
        user, headers = test_user
        _create_resume(db_session, user.id, "Solo Resume", completed=True)

        r = client.get("/api/dashboard/summary", headers=headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert not data["is_empty"]
        assert data["resume"]["count"] == 1
        assert data["job_stats"]["total_applications"] == 0
        assert data["interview"]["total_sessions"] == 0
        assert data["career_readiness"] is None
        assert data["recent_activity"] == []
