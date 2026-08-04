"""Tests for the Activity logging module."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.activity.models import ActivityEvent
from app.activity.service import ActivityService
from app.activity.constants import EventType


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
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# Unit: ActivityService
# ---------------------------------------------------------------------------

class TestActivityService:

    def test_log_event_creates_record(self, db_session):
        ActivityService.log_event(
            db_session, user_id=1, event_type=EventType.RESUME_CREATED,
            title="Test event", description="Test desc",
            related_entity_type="resume", related_entity_id=42,
        )
        events = db_session.query(ActivityEvent).all()
        assert len(events) == 1
        assert events[0].event_type == "resume_created"
        assert events[0].title == "Test event"
        assert events[0].description == "Test desc"
        assert events[0].related_entity_type == "resume"
        assert events[0].related_entity_id == 42
        assert events[0].user_id == 1

    def test_get_recent_returns_most_recent_first(self, db_session):
        import time
        for i in range(5):
            ActivityService.log_event(db_session, user_id=1,
                event_type=EventType.RESUME_CREATED, title=f"Event {i}")
            time.sleep(0.005)
        recent = ActivityService.get_recent(db_session, user_id=1, limit=3)
        assert len(recent) == 3
        titles = [e.title for e in recent]
        assert titles == ["Event 4", "Event 3", "Event 2"]

    def test_get_recent_scoped_by_user(self, db_session):
        ActivityService.log_event(db_session, user_id=1,
            event_type=EventType.RESUME_CREATED, title="User 1 event")
        ActivityService.log_event(db_session, user_id=2,
            event_type=EventType.RESUME_CREATED, title="User 2 event")
        recent = ActivityService.get_recent(db_session, user_id=1)
        assert len(recent) == 1
        assert recent[0].title == "User 1 event"

    def test_log_event_resilient_on_failure(self, db_session):
        """log_event must not raise even if something goes wrong inside."""
        original_add = db_session.add
        def broken_add(obj):
            raise RuntimeError("DB write failed")
        db_session.add = broken_add
        try:
            ActivityService.log_event(
                db_session, user_id=1, event_type=EventType.RESUME_CREATED,
                title="Should not crash",
            )
        finally:
            db_session.add = original_add

    def test_log_event_stores_job_application_link(self, db_session):
        ActivityService.log_event(
            db_session, user_id=1, event_type=EventType.COMMUNICATION_MESSAGE_CREATED,
            title="Message", related_entity_type="communication",
            related_entity_id=7, related_job_application_id=42,
        )
        event = db_session.query(ActivityEvent).one()
        assert event.related_job_application_id == 42

    def test_list_events_orders_newest_first(self, db_session):
        import time
        for i in range(4):
            ActivityService.log_event(db_session, user_id=1,
                event_type=EventType.RESUME_CREATED, title=f"E{i}")
            time.sleep(0.005)
        items, total = ActivityService.list_events(db_session, user_id=1)
        assert total == 4
        assert [e.title for e in items] == ["E3", "E2", "E1", "E0"]

    def test_list_events_filter_by_event_type(self, db_session):
        ActivityService.log_event(db_session, user_id=1,
            event_type=EventType.RESUME_CREATED, title="Resume")
        ActivityService.log_event(db_session, user_id=1,
            event_type=EventType.JOB_APPLICATION_CREATED, title="Job")
        items, total = ActivityService.list_events(
            db_session, user_id=1, event_type="job_application_created")
        assert total == 1
        assert items[0].title == "Job"

    def test_list_events_filter_by_job_application(self, db_session):
        ActivityService.log_event(db_session, user_id=1,
            event_type=EventType.COMMUNICATION_MESSAGE_CREATED, title="For app 5",
            related_job_application_id=5)
        ActivityService.log_event(db_session, user_id=1,
            event_type=EventType.COMMUNICATION_MESSAGE_CREATED, title="For app 9",
            related_job_application_id=9)
        items, total = ActivityService.list_events(
            db_session, user_id=1, job_application_id=5)
        assert total == 1
        assert items[0].title == "For app 5"

    def test_list_events_scoped_by_user(self, db_session):
        ActivityService.log_event(db_session, user_id=1,
            event_type=EventType.RESUME_CREATED, title="User 1")
        ActivityService.log_event(db_session, user_id=2,
            event_type=EventType.RESUME_CREATED, title="User 2")
        items, total = ActivityService.list_events(db_session, user_id=2)
        assert total == 1
        assert items[0].title == "User 2"

    def test_list_events_pagination(self, db_session):
        import time
        for i in range(5):
            ActivityService.log_event(db_session, user_id=1,
                event_type=EventType.RESUME_CREATED, title=f"E{i}")
            time.sleep(0.005)
        first, total = ActivityService.list_events(db_session, user_id=1, limit=2, offset=0)
        second, _ = ActivityService.list_events(db_session, user_id=1, limit=2, offset=2)
        assert total == 5
        assert [e.title for e in first] == ["E4", "E3"]
        assert [e.title for e in second] == ["E2", "E1"]


# ---------------------------------------------------------------------------
# API: GET /api/activity/recent
# ---------------------------------------------------------------------------

class TestActivityApi:

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
        from app.models.user import User
        from app.dependencies import get_password_hash, create_access_token
        user = User(
            email="act_test@test.com",
            username="act_test",
            hashed_password=get_password_hash("Test1234!"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        token = create_access_token(data={"sub": str(user.id)})
        return user, {"Authorization": f"Bearer {token}"}

    def test_get_recent_empty(self, client, test_user):
        _, headers = test_user
        r = client.get("/api/activity/recent", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["items"] == []

    def test_get_recent_returns_events(self, client, test_user, db_session):
        user, headers = test_user
        ActivityService.log_event(
            db_session, user.id, EventType.RESUME_CREATED,
            title="Test resume",
        )
        r = client.get("/api/activity/recent", headers=headers)
        assert r.status_code == 200
        items = r.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["event_type"] == "resume_created"
        assert items[0]["title"] == "Test resume"

    def test_get_recent_scoped_per_user(self, client, test_user, db_session):
        user_a, headers_a = test_user
        from app.models.user import User
        from app.dependencies import get_password_hash, create_access_token
        user_b = User(
            email="act_user_b@test.com", username="act_user_b",
            hashed_password=get_password_hash("Test1234!"), is_active=True,
        )
        db_session.add(user_b)
        db_session.commit()
        db_session.refresh(user_b)
        headers_b = {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_b.id)})}"}

        ActivityService.log_event(db_session, user_a.id,
            EventType.RESUME_CREATED, title="A resume")
        ActivityService.log_event(db_session, user_b.id,
            EventType.RESUME_CREATED, title="B resume")

        r_a = client.get("/api/activity/recent", headers=headers_a)
        r_b = client.get("/api/activity/recent", headers=headers_b)
        assert r_a.status_code == 200
        assert r_b.status_code == 200
        assert len(r_a.json()["data"]["items"]) == 1
        assert r_a.json()["data"]["items"][0]["title"] == "A resume"
        assert len(r_b.json()["data"]["items"]) == 1
        assert r_b.json()["data"]["items"][0]["title"] == "B resume"


# ---------------------------------------------------------------------------
# Resilience
# ---------------------------------------------------------------------------

class TestResilience:

    def test_resume_create_succeeds_even_if_logging_fails(self, db_session):
        """The original operation must succeed even if log_event raises."""
        from app.models.resume import Resume
        original_add = db_session.add
        call_count = 0

        def tracking_add(obj):
            nonlocal call_count
            call_count += 1
            if isinstance(obj, ActivityEvent):
                raise RuntimeError("Simulated log failure")
            return original_add(obj)

        db_session.add = tracking_add
        try:
            resume = Resume(user_id=999, name="Resilient Resume")
            db_session.add(resume)
            db_session.commit()
            db_session.refresh(resume)
            ActivityService.log_event(
                db_session, 999, EventType.RESUME_CREATED,
                title="Should not break",
            )
            assert resume.id is not None
            assert resume.name == "Resilient Resume"
        finally:
            db_session.add = original_add


# ---------------------------------------------------------------------------
# API: GET /api/activity (full feed)
# ---------------------------------------------------------------------------

class TestActivityFeedApi:

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
        from app.models.user import User
        from app.dependencies import get_password_hash, create_access_token
        user = User(
            email="act_feed@test.com",
            username="act_feed",
            hashed_password=get_password_hash("Test1234!"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        token = create_access_token(data={"sub": str(user.id)})
        return user, {"Authorization": f"Bearer {token}"}

    def test_feed_requires_auth(self, client):
        r = client.get("/api/activity")
        assert r.status_code in (401, 403)

    def test_feed_empty(self, client, test_user):
        _, headers = test_user
        r = client.get("/api/activity", headers=headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_more"] is False

    def test_feed_returns_events_ordered(self, client, test_user, db_session):
        import time
        user, headers = test_user
        for i in range(3):
            ActivityService.log_event(
                db_session, user.id, EventType.RESUME_CREATED, title=f"Resume {i}")
            time.sleep(0.005)
        r = client.get("/api/activity", headers=headers)
        assert r.status_code == 200
        items = r.json()["data"]["items"]
        assert [i["title"] for i in items] == ["Resume 2", "Resume 1", "Resume 0"]
        assert all(i["event_type"] == "resume_created" for i in items)

    def test_feed_includes_job_application_link(self, client, test_user, db_session):
        user, headers = test_user
        ActivityService.log_event(
            db_session, user.id, EventType.COMMUNICATION_MESSAGE_CREATED,
            title="Linked message", related_job_application_id=11)
        r = client.get("/api/activity", headers=headers)
        item = r.json()["data"]["items"][0]
        assert item["related_job_application_id"] == 11

    def test_feed_filter_by_event_type(self, client, test_user, db_session):
        user, headers = test_user
        ActivityService.log_event(db_session, user.id,
            EventType.RESUME_CREATED, title="Resume")
        ActivityService.log_event(db_session, user.id,
            EventType.JOB_APPLICATION_CREATED, title="Job")
        r = client.get("/api/activity?event_type=job_application_created", headers=headers)
        items = r.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Job"

    def test_feed_filter_by_job_application(self, client, test_user, db_session):
        user, headers = test_user
        ActivityService.log_event(db_session, user.id,
            EventType.COMMUNICATION_MESSAGE_CREATED, title="App 3",
            related_job_application_id=3)
        ActivityService.log_event(db_session, user.id,
            EventType.COMMUNICATION_MESSAGE_CREATED, title="App 4",
            related_job_application_id=4)
        r = client.get("/api/activity?job_application_id=4", headers=headers)
        items = r.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["title"] == "App 4"

    def test_feed_pagination_has_more(self, client, test_user, db_session):
        import time
        user, headers = test_user
        for i in range(4):
            ActivityService.log_event(db_session, user.id,
                EventType.RESUME_CREATED, title=f"E{i}")
            time.sleep(0.005)
        r = client.get("/api/activity?limit=2&offset=0", headers=headers)
        data = r.json()["data"]
        assert len(data["items"]) == 2
        assert data["total"] == 4
        assert data["has_more"] is True


# ---------------------------------------------------------------------------
# Cross-module integration: one real action per module lands on the feed
# ---------------------------------------------------------------------------

class TestCrossModuleFeed:

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
        from app.models.user import User
        from app.dependencies import get_password_hash, create_access_token
        user = User(
            email="act_xmodule@test.com",
            username="act_xmodule",
            hashed_password=get_password_hash("Test1234!"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        token = create_access_token(data={"sub": str(user.id)})
        return user, {"Authorization": f"Bearer {token}"}

    def test_one_action_per_module_appears_on_feed(self, client, test_user, db_session):
        user, headers = test_user

        # --- Resume: create ---
        from app.services.resume_service import ResumeService
        from app.schemas.resume import ResumeCreate
        resume = ResumeService.create(
            db_session, user.id, ResumeCreate(name="QA Resume", summary="Software engineer"))

        # --- Job tracker: create + status change ---
        from app.job_tracker.services.job_tracker_service import JobTrackerService
        from app.schemas.job_tracker import (
            JobApplicationCreate, JobApplicationUpdate, JobStatus,
        )
        job = JobTrackerService.create_job(
            db_session, user.id,
            JobApplicationCreate(
                company="Acme", job_title="Backend Engineer", status=JobStatus.WISHLIST,
                job_description="Python backend role",
            ),
        )
        JobTrackerService.update_job(
            db_session, job.id, user.id,
            JobApplicationUpdate(status=JobStatus.INTERVIEW),
        )

        # --- Cover letter: create (linked to the application) ---
        from app.services.cover_letter_service import CoverLetterService
        from app.schemas.cover_letter import CoverLetterCreate
        CoverLetterService.create(
            db_session, user.id,
            CoverLetterCreate(
                title="Acme Cover Letter", job_title="Backend Engineer",
                company_name="Acme", resume_id=resume.id,
                job_application_id=job.id,
            ),
        )

        # --- Communication: outbound created + inbound logged ---
        from app.communication.service import CommunicationService
        from app.communication.schemas import CommunicationMessageCreate
        CommunicationService.create(
            db_session, user.id,
            CommunicationMessageCreate(
                message_type="cold_email", subject="Application follow-up",
                body="Following up on my application.",
                related_job_application_id=job.id,
            ),
        )
        CommunicationService.log_inbound(
            db_session, user.id, related_job_application_id=job.id,
            subject="Interview invitation", body="We would like to schedule an interview.",
        )

        # --- Interview: practice session started + completed (scored) ---
        from app.interview_prep.service import InterviewPrepService
        from app.interview_prep.schemas import CreateSessionRequest, UpdateSessionRequest
        session = InterviewPrepService.create_session(
            db_session, user.id,
            CreateSessionRequest(
                job_title="Backend Engineer", question_count=3,
                related_job_application_id=job.id,
            ),
        )
        InterviewPrepService.update_session(
            db_session, user.id, session.id,
            UpdateSessionRequest(overall_score=82),
        )

        # --- JD match: deterministic (no AI) against the saved application ---
        r = client.post("/api/jd-match/analyze", headers=headers, json={
            "jd_text": "Backend Engineer with Python and SQL",
            "resume_data": {
                "skills": ["Python", "SQL", "Django"],
                "summary": "Software engineer",
                "experience": [],
                "education": [],
            },
            "enable_ai": False,
            "job_application_id": job.id,
        })
        assert r.status_code == 200

        # --- Feed must contain every module's event ---
        r = client.get("/api/activity", headers=headers)
        assert r.status_code == 200
        data = r.json()["data"]
        types = {i["event_type"] for i in data["items"]}

        assert "resume_created" in types
        assert "job_application_created" in types
        assert "job_application_status_changed" in types
        assert "cover_letter_created" in types
        assert "communication_message_created" in types
        assert "communication_message_received" in types
        assert "interview_session_created" in types
        assert "interview_session_completed" in types
        assert "jd_match_analyzed" in types

        # Newest-first ordering, and the whole feed is one chronological view.
        timestamps = [i["created_at"] for i in data["items"]]
        assert timestamps == sorted(timestamps, reverse=True)

        # Application-linked events carry the link for click-through.
        app_linked = [i for i in data["items"] if i["related_job_application_id"] == job.id]
        assert len(app_linked) >= 6
