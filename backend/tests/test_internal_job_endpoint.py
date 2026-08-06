"""Tests for the internal daily-suggestion trigger endpoint.

The daily follow-up-suggestion job used to run on an in-process APScheduler
job inside the web process. It is now triggered only by
POST /api/internal/run-daily-suggestions, authenticated with a shared secret
in the X-Internal-Secret header (NOT the user JWT). These tests confirm:

- The endpoint runs the exact suggestion logic with the correct secret.
- It rejects missing / wrong secrets with 401.
- It fails closed (503) when the secret is not configured at all.
- A normal user JWT cannot bypass the shared-secret check.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_SECRET = "unit-test-internal-job-secret"


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

def _create_user(db, email="internal@test.com", username="internaltester",
                 password="Test1234!"):
    from app.dependencies import get_password_hash
    from app.models.user import User
    u = User(email=email, username=username,
             hashed_password=get_password_hash(password), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_stale_job(db, user_id, days_ago=8, status="Applied"):
    from app.models.job_application import JobApplication
    from app.schemas.job_tracker import JobStatus
    stale_cutoff = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        - timedelta(days=days_ago)
    )
    j = JobApplication(
        user_id=user_id, company="Acme", job_title="Engineer",
        status=JobStatus(status),
        updated_at=stale_cutoff,
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def _create_fresh_job(db, user_id, status="Applied"):
    from app.models.job_application import JobApplication
    from app.schemas.job_tracker import JobStatus
    j = JobApplication(
        user_id=user_id, company="FreshCo", job_title="Engineer",
        status=JobStatus(status),
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def _secret_headers():
    return {"X-Internal-Secret": TEST_SECRET}


# ---------------------------------------------------------------------------
# Endpoint behavior
# ---------------------------------------------------------------------------

class TestRunDailySuggestionsEndpoint:

    def test_runs_logic_with_correct_secret(self, db_session, client, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_JOB_SECRET", TEST_SECRET)
        user = _create_user(db_session)
        stale = _create_stale_job(db_session, user.id)
        _create_fresh_job(db_session, user.id)

        resp = client.post("/api/internal/run-daily-suggestions", headers=_secret_headers())
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["suggestions_created"] == 1

        from app.communication.models import CommunicationSuggestion
        suggestion = db_session.query(CommunicationSuggestion).filter_by(
            job_application_id=stale.id
        ).first()
        assert suggestion is not None
        assert suggestion.suggestion_type == "follow_up_due"
        assert suggestion.is_actioned is False

    def test_does_not_duplicate_suggestions(self, db_session, client, monkeypatch):
        """Calling the endpoint twice creates the suggestion only once — the
        same dedup behavior the old scheduler job had."""
        monkeypatch.setattr(settings, "INTERNAL_JOB_SECRET", TEST_SECRET)
        user = _create_user(db_session)
        _create_stale_job(db_session, user.id)

        first = client.post("/api/internal/run-daily-suggestions", headers=_secret_headers())
        second = client.post("/api/internal/run-daily-suggestions", headers=_secret_headers())
        assert first.status_code == 200
        assert first.json()["data"]["suggestions_created"] == 1
        assert second.status_code == 200
        assert second.json()["data"]["suggestions_created"] == 0

    def test_rejects_missing_secret(self, db_session, client, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_JOB_SECRET", TEST_SECRET)
        resp = client.post("/api/internal/run-daily-suggestions")
        assert resp.status_code == 401

    def test_rejects_wrong_secret(self, db_session, client, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_JOB_SECRET", TEST_SECRET)
        resp = client.post(
            "/api/internal/run-daily-suggestions",
            headers={"X-Internal-Secret": "not-the-secret"},
        )
        assert resp.status_code == 401

    def test_rejects_when_secret_not_configured(self, db_session, client, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_JOB_SECRET", "")
        resp = client.post(
            "/api/internal/run-daily-suggestions",
            headers={"X-Internal-Secret": "anything"},
        )
        assert resp.status_code == 503

    def test_user_jwt_cannot_bypass_secret(self, db_session, client, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_JOB_SECRET", TEST_SECRET)
        user = _create_user(db_session)
        token = _login(client, email=user.email)

        resp = client.post(
            "/api/internal/run-daily-suggestions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


def _login(client, email="internal@test.com", password="Test1234!"):
    resp = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
