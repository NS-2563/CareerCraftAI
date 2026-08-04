"""Tests for the Communication conversation-thread feature.

Covers:
- POST /api/communication/log-inbound  (ownership-scoped inbound logging)
- GET  /api/communication/thread/{id}   (chronological, ownership-scoped)
- Recruiter-reply generation pulling recent thread context
- IDOR: a second user cannot log to / read another user's application
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dependencies import create_access_token
from app.communication.service import CommunicationService


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


def _create_job_application(db, user_id, company="Acme", job_title="Engineer"):
    from app.models.job_application import JobApplication
    from app.schemas.job_tracker import JobStatus
    j = JobApplication(
        user_id=user_id, company=company, job_title=job_title,
        status=JobStatus("Applied"),
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


class _FakeProvider:
    """Stand-in for the AI provider to capture recruiter_reply arguments."""

    def __init__(self):
        self.calls = []

    def generate_recruiter_reply(self, inbound_message=None, reply_intent=None,
                                 recipient_name=None, recipient_company=None,
                                 tone=None, custom_context=None,
                                 thread_context=None, **kwargs):
        self.calls.append({
            "inbound_message": inbound_message,
            "reply_intent": reply_intent,
            "recipient_name": recipient_name,
            "recipient_company": recipient_company,
            "thread_context": thread_context,
        })
        return {"subject": "Re: Interview", "body": "Generated reply body"}


# ---------------------------------------------------------------------------
# Unit: CommunicationService thread helpers
# ---------------------------------------------------------------------------

class TestThreadService:

    def test_get_thread_orders_chronologically(self, db_session):
        from datetime import datetime, timedelta
        from app.communication.models import CommunicationMessage

        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)

        def _msg(body, when):
            m = CommunicationMessage(
                user_id=user.id, message_type="recruiter_email", tone="professional",
                direction="inbound", body=body,
                related_job_application_id=job.id,
                version=1, version_history="[]",
            )
            db_session.add(m)
            db_session.commit()
            db_session.refresh(m)
            m.created_at = when
            db_session.commit()
            return m

        earlier = _msg("First email", datetime(2026, 1, 1, 9, 0, 0))
        later = _msg("Second email", datetime(2026, 1, 2, 9, 0, 0))

        thread = CommunicationService.get_thread(db_session, user.id, job.id)
        assert [m.id for m in thread] == [earlier.id, later.id]

    def test_get_thread_scoped_to_user_and_application(self, db_session):
        from app.communication.models import CommunicationMessage

        user_a = _create_user(db_session, email="a@test.com", username="usera")
        user_b = _create_user(db_session, email="b@test.com", username="userb")
        job_a = _create_job_application(db_session, user_a.id, "Acme")
        job_b = _create_job_application(db_session, user_b.id, "Beta")

        def _msg(user_id, job_id, body):
            m = CommunicationMessage(
                user_id=user_id, message_type="recruiter_email", tone="professional",
                direction="inbound", body=body,
                related_job_application_id=job_id,
                version=1, version_history="[]",
            )
            db_session.add(m)
            db_session.commit()
            db_session.refresh(m)
            return m

        a_msg = _msg(user_a.id, job_a.id, "A's message")
        _msg(user_b.id, job_b.id, "B's message")

        assert [m.id for m in CommunicationService.get_thread(db_session, user_a.id, job_a.id)] == [a_msg.id]
        assert CommunicationService.get_thread(db_session, user_a.id, job_b.id) == []
        assert CommunicationService.get_thread(db_session, user_b.id, job_a.id) == []

    def test_get_recent_thread_returns_last_n_chronological(self, db_session):
        from app.communication.models import CommunicationMessage

        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)

        for i in range(8):
            db_session.add(CommunicationMessage(
                user_id=user.id, message_type="recruiter_email", tone="professional",
                direction="inbound", body=f"msg {i}",
                related_job_application_id=job.id,
                version=1, version_history="[]",
            ))
        db_session.commit()

        recent = CommunicationService.get_recent_thread(db_session, user.id, job.id, n=5)
        assert [m.body for m in recent] == ["msg 3", "msg 4", "msg 5", "msg 6", "msg 7"]

    def test_log_inbound_sets_direction_and_type(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)

        msg = CommunicationService.log_inbound(
            db=db_session,
            user_id=user.id,
            related_job_application_id=job.id,
            body="Pasted recruiter email",
            sender_name="Sarah",
            sender_email="sarah@acme.com",
            subject="Interview invite",
        )

        assert msg.message_type == "recruiter_email"
        assert msg.direction == "inbound"
        assert msg.sender_name == "Sarah"
        assert msg.sender_email == "sarah@acme.com"
        assert msg.subject == "Interview invite"
        assert msg.related_job_application_id == job.id


# ---------------------------------------------------------------------------
# API: log-inbound + thread
# ---------------------------------------------------------------------------

class TestThreadApi:

    @pytest.fixture
    def client(self, db_session):
        def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def _auth(self, user):
        token = create_access_token(data={"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    def test_log_inbound_requires_auth(self, client):
        r = client.post("/api/communication/log-inbound", json={
            "related_job_application_id": 1, "body": "hello",
        })
        assert r.status_code == 401

    def test_thread_requires_auth(self, client):
        r = client.get("/api/communication/thread/1")
        assert r.status_code == 401

    def test_log_inbound_creates_message(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)

        r = client.post("/api/communication/log-inbound", headers=headers, json={
            "related_job_application_id": job.id,
            "sender_name": "Sarah Recruiter",
            "sender_email": "sarah@acme.com",
            "subject": "Interview invite",
            "body": "Hi, we'd love to schedule an interview.",
        })

        assert r.status_code == 201
        data = r.json()
        assert data["direction"] == "inbound"
        assert data["message_type"] == "recruiter_email"
        assert data["sender_name"] == "Sarah Recruiter"
        assert data["related_job_application_id"] == job.id

    def test_log_inbound_foreign_application_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job_application(db_session, owner.id, "OwnerCo")

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = self._auth(attacker)

        r = client.post("/api/communication/log-inbound", headers=headers, json={
            "related_job_application_id": job.id,
            "body": "tamper",
        })
        assert r.status_code == 404

    def test_log_inbound_unknown_application_returns_404(self, client, db_session):
        user = _create_user(db_session)
        headers = self._auth(user)

        r = client.post("/api/communication/log-inbound", headers=headers, json={
            "related_job_application_id": 999999,
            "body": "hello",
        })
        assert r.status_code == 404

    def test_thread_returns_chronological_messages(self, client, db_session):
        from app.communication.models import CommunicationMessage

        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)

        for i, body in enumerate(["first", "second", "third"]):
            db_session.add(CommunicationMessage(
                user_id=user.id, message_type="recruiter_email", tone="professional",
                direction="inbound", body=body,
                related_job_application_id=job.id,
                version=1, version_history="[]",
            ))
        db_session.commit()

        r = client.get(f"/api/communication/thread/{job.id}", headers=headers)
        assert r.status_code == 200
        bodies = [m["body"] for m in r.json()]
        assert bodies == ["first", "second", "third"]

    def test_thread_foreign_application_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job_application(db_session, owner.id, "OwnerCo")

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = self._auth(attacker)

        r = client.get(f"/api/communication/thread/{job.id}", headers=headers)
        assert r.status_code == 404

    def test_thread_unknown_application_returns_404(self, client, db_session):
        user = _create_user(db_session)
        headers = self._auth(user)
        r = client.get("/api/communication/thread/999999", headers=headers)
        assert r.status_code == 404

    def test_outbound_reply_saves_with_application_and_direction(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)

        r = client.post("/api/communication", headers=headers, json={
            "message_type": "recruiter_reply",
            "tone": "professional",
            "recipient_name": "Sarah Recruiter",
            "recipient_company": "Acme",
            "subject": "Re: Interview",
            "body": "Thanks for the invite!",
            "related_job_application_id": job.id,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["direction"] == "outbound"
        assert data["related_job_application_id"] == job.id


# ---------------------------------------------------------------------------
# Recruiter reply with thread context
# ---------------------------------------------------------------------------

class TestThreadAwareReply:

    @pytest.fixture
    def client(self, db_session, monkeypatch):
        fake = _FakeProvider()
        monkeypatch.setattr("app.communication.router.get_provider", lambda: fake)

        def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override
        client = TestClient(app)
        client._fake_provider = fake
        yield client
        app.dependency_overrides.clear()

    def _auth(self, user):
        token = create_access_token(data={"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    def _seed_thread(self, db_session, user, job, count):
        from app.communication.models import CommunicationMessage
        bodies = []
        for i in range(count):
            bodies.append(f"thread message {i}")
            db_session.add(CommunicationMessage(
                user_id=user.id, message_type="recruiter_email", tone="professional",
                direction="inbound", body=bodies[-1],
                related_job_application_id=job.id,
                version=1, version_history="[]",
            ))
        db_session.commit()
        return bodies

    def test_reply_generation_includes_recent_thread_context(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)
        self._seed_thread(db_session, user, job, 8)

        r = client.post("/api/communication/generate", headers=headers, json={
            "message_type": "recruiter_reply",
            "reply_intent": "accept_interest",
            "recipient_name": "Sarah Recruiter",
            "recipient_company": "Acme",
            "inbound_message": "Would Monday 10am work?",
            "related_job_application_id": job.id,
        })

        assert r.status_code == 201
        call = client._fake_provider.calls[-1]
        assert call["inbound_message"] == "Would Monday 10am work?"
        assert call["reply_intent"] == "accept_interest"
        # Thread context = last 5 messages in chronological order
        assert call["thread_context"] is not None
        assert len(call["thread_context"]) == 5
        assert call["thread_context"][0]["body"] == "thread message 3"
        assert call["thread_context"][-1]["body"] == "thread message 7"

    def test_reply_without_application_gets_no_thread_context(self, client, db_session):
        user = _create_user(db_session)
        headers = self._auth(user)

        r = client.post("/api/communication/generate", headers=headers, json={
            "message_type": "recruiter_reply",
            "reply_intent": "decline_politely",
            "inbound_message": "Sorry to inform you the role is closed.",
        })

        assert r.status_code == 201
        call = client._fake_provider.calls[-1]
        assert call["thread_context"] is None

    def test_thread_context_respects_thread_context_false(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)
        self._seed_thread(db_session, user, job, 3)

        r = client.post("/api/communication/generate", headers=headers, json={
            "message_type": "recruiter_reply",
            "reply_intent": "ask_clarifying_questions",
            "recipient_name": "Sarah Recruiter",
            "inbound_message": "Could you clarify the team size?",
            "related_job_application_id": job.id,
            "thread_context": False,
        })

        assert r.status_code == 201
        call = client._fake_provider.calls[-1]
        assert call["thread_context"] is None

    def test_thread_context_not_leaked_to_other_users_application(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job_application(db_session, owner.id, "OwnerCo")
        self._seed_thread(db_session, owner, job, 3)

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = self._auth(attacker)

        # Foreign application: even if supplied, thread context must not resolve.
        r = client.post("/api/communication/generate", headers=headers, json={
            "message_type": "recruiter_reply",
            "reply_intent": "accept_interest",
            "inbound_message": "Hi from the attacker",
            "related_job_application_id": job.id,
        })

        assert r.status_code == 201
        call = client._fake_provider.calls[-1]
        assert call["thread_context"] is None
