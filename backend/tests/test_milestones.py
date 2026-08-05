"""Tests for Career Milestones — first-occurrence achievements derived strictly
from real Activity Log events (never fabricated)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dashboard.milestones import (
    MILESTONES,
    detect_milestones,
)


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


@pytest.fixture
def client(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, email, username, password="Test1234!"):
    from app.dependencies import get_password_hash
    from app.models.user import User
    u = User(email=email, username=username,
             hashed_password=get_password_hash(password), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _activity(db, user_id, event_type, title="title", description=None):
    from datetime import datetime, timedelta, timezone
    from app.activity.models import ActivityEvent
    db.add(ActivityEvent(
        user_id=user_id, event_type=event_type, title=title,
        description=description,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=len(title)),
    ))
    db.commit()


def _login(client, email, password="Test1234!"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Unit
# ---------------------------------------------------------------------------

class TestDetectMilestones:

    def test_no_events_all_not_achieved(self, db_session):
        u = _create_user(db_session, "none@ms.com", "nonems")
        milestones = detect_milestones(db_session, u.id)
        assert len(milestones) == len(MILESTONES)
        assert all(m["achieved"] is False for m in milestones)
        assert all(m["achieved_at"] is None for m in milestones)

    def test_first_resume_event_achieves_first_resume(self, db_session):
        u = _create_user(db_session, "res@ms.com", "resms")
        _event = _activity(db_session, u.id, "resume_created")
        milestones = {m["key"]: m for m in detect_milestones(db_session, u.id)}
        assert milestones["first_resume"]["achieved"] is True
        assert milestones["first_resume"]["achieved_at"] is not None

    def test_achieves_first_occurrence_only(self, db_session):
        u = _create_user(db_session, "first@ms.com", "firstms")
        _activity(db_session, u.id, "job_application_created")
        milestones = {m["key"]: m for m in detect_milestones(db_session, u.id)}
        assert milestones["first_application"]["achieved"] is True
        assert milestones["first_resume"]["achieved"] is False

    def test_imported_variant_achieves_first_resume(self, db_session):
        u = _create_user(db_session, "imp@ms.com", "import")
        _activity(db_session, u.id, "resume_imported")
        milestones = {m["key"]: m for m in detect_milestones(db_session, u.id)}
        assert milestones["first_resume"]["achieved"] is True

    def test_scoped_per_user(self, db_session):
        u_a = _create_user(db_session, "scopea@ms.com", "scopemsa")
        u_b = _create_user(db_session, "scopeb@ms.com", "scopemsb")
        _activity(db_session, u_a.id, "resume_created")
        a = {m["key"]: m for m in detect_milestones(db_session, u_a.id)}
        b = {m["key"]: m for m in detect_milestones(db_session, u_b.id)}
        assert a["first_resume"]["achieved"] is True
        assert b["first_resume"]["achieved"] is False

    def test_all_defined_event_types_are_valid(self):
        from app.activity.constants import EVENT_TYPE_CHOICES
        valid = set(EVENT_TYPE_CHOICES)
        for m in MILESTONES:
            for t in m["event_types"]:
                assert t in valid, f"unknown event type {t} for {m['key']}"


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class TestMilestonesApi:

    def test_requires_auth(self, client):
        resp = client.get("/api/dashboard/milestones")
        assert resp.status_code == 401

    def test_returns_milestones_for_user(self, db_session, client):
        u = _create_user(db_session, "msapi@home.com", "msapi")
        _activity(db_session, u.id, "resume_created")
        _activity(db_session, u.id, "jd_match_analyzed")
        token = _login(client, "msapi@home.com")
        resp = client.get(
            "/api/dashboard/milestones",
            headers=_headers(token),
        )
        assert resp.status_code == 200, resp.text
        milestones = resp.json()["data"]["milestones"]
        assert len(milestones) == len(MILESTONES)
        by_key = {m["key"]: m for m in milestones}
        assert by_key["first_resume"]["achieved"] is True
        assert by_key["first_jd_match"]["achieved"] is True
        assert by_key["first_application"]["achieved"] is False