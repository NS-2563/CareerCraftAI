"""Tests for the deterministic per-application thread summary + generation_method.

Covers:
- compute_thread_summary: pure derivations (last reply, last recruiter email,
  overdue boundary at exactly N days, order-independence, determinism)
- generation_method provenance per creation path
  (manual create / AI generate / manual inbound / duplicate)
- API: thread and list responses carry thread_summary + generation_method
- API: interview sessions-for-application endpoint (timeline interleave source)
"""

import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dependencies import create_access_token
from app.communication.service import CommunicationService
from app.communication.thread_summary import (
    compute_thread_summary,
    attach_thread_summary,
    EMPTY_SUMMARY,
    STATE_WAITING,
    STATE_NEEDS_REPLY,
    STATE_RESPONSE_OVERDUE,
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


def _brief_msg(msg_id, direction, created_at, **kwargs):
    return SimpleNamespace(
        id=msg_id,
        direction=direction,
        created_at=created_at,
        sender_name=kwargs.get("sender_name"),
        sender_email=kwargs.get("sender_email"),
        recipient_name=kwargs.get("recipient_name"),
        message_type=kwargs.get("message_type", "recruiter_email"),
        subject=kwargs.get("subject"),
    )


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Pure: compute_thread_summary
# ---------------------------------------------------------------------------

class TestThreadSummaryPure:

    def test_empty_thread_returns_empty_summary(self):
        summary = compute_thread_summary([])
        assert summary["has_thread"] is False
        assert summary["state"] == "none"
        assert summary["last_reply"] is None
        assert summary["last_recruiter_email"] is None
        assert summary["response_overdue"] is False
        assert summary["response_overdue_days"] is None

    def test_single_outbound_is_waiting(self):
        now = _now()
        summary = compute_thread_summary([
            _brief_msg(1, "outbound", now, sender_name="Me", subject="Intro"),
        ])
        assert summary["has_thread"] is True
        assert summary["last_message_direction"] == "outbound"
        assert summary["state"] == STATE_WAITING
        assert summary["response_overdue"] is False
        assert summary["last_reply"]["id"] == 1
        assert summary["last_recruiter_email"] is None

    def test_single_inbound_is_needs_reply(self):
        now = _now()
        summary = compute_thread_summary([
            _brief_msg(1, "inbound", now, sender_name="Sarah"),
        ])
        assert summary["state"] == STATE_NEEDS_REPLY
        assert summary["last_recruiter_email"]["sender_name"] == "Sarah"
        assert summary["response_overdue"] is False

    def test_inbound_exactly_n_days_old_not_overdue(self):
        # Boundary: at exactly COMMUNICATION_OVERDUE_AFTER_DAYS (5) days, NOT overdue.
        old = _now() - timedelta(days=5)
        summary = compute_thread_summary([
            _brief_msg(1, "inbound", old, sender_name="Sarah"),
        ])
        assert summary["state"] == STATE_NEEDS_REPLY
        assert summary["response_overdue"] is False
        assert summary["response_overdue_days"] is None

    def test_inbound_after_n_days_is_overdue(self):
        # Day 6 -> strictly greater than threshold -> overdue.
        old = _now() - timedelta(days=6)
        summary = compute_thread_summary([
            _brief_msg(1, "inbound", old, sender_name="Sarah"),
        ])
        assert summary["state"] == STATE_RESPONSE_OVERDUE
        assert summary["response_overdue"] is True
        assert summary["response_overdue_days"] == 6

    def test_inbound_long_overdue_reports_days(self):
        old = _now() - timedelta(days=20)
        summary = compute_thread_summary([
            _brief_msg(1, "inbound", old, sender_name="Sarah"),
        ])
        assert summary["response_overdue"] is True
        assert summary["response_overdue_days"] == 20

    def test_reply_after_inbound_clears_overdue(self):
        old = _now() - timedelta(days=10)
        now = _now()
        summary = compute_thread_summary([
            _brief_msg(1, "inbound", old, sender_name="Sarah"),
            _brief_msg(2, "outbound", now, sender_name="Me", subject="Re: Hello"),
        ])
        assert summary["state"] == STATE_WAITING
        assert summary["response_overdue"] is False
        # last recruiter email still surfaces the most recent inbound
        assert summary["last_recruiter_email"]["id"] == 1

    def test_missing_created_at_never_overdue(self):
        summary = compute_thread_summary([
            _brief_msg(1, "inbound", None, sender_name="Sarah"),
        ])
        assert summary["state"] == STATE_NEEDS_REPLY
        assert summary["response_overdue"] is False
        assert summary["response_overdue_days"] is None

    def test_last_recruiter_email_is_most_recent_inbound(self):
        now = _now()
        summary = compute_thread_summary([
            _brief_msg(1, "inbound", now - timedelta(days=2), sender_name="Old"),
            _brief_msg(2, "outbound", now - timedelta(days=1), sender_name="Me"),
            _brief_msg(3, "inbound", now, sender_name="New"),
        ])
        assert summary["last_reply"]["id"] == 3
        assert summary["last_recruiter_email"]["id"] == 3

    def test_reply_outbound_surfaces_older_inbound_recruiter_email(self):
        now = _now()
        summary = compute_thread_summary([
            _brief_msg(1, "inbound", now - timedelta(days=1), sender_name="Sarah"),
            _brief_msg(2, "outbound", now, sender_name="Me"),
        ])
        assert summary["last_reply"]["id"] == 2
        assert summary["last_recruiter_email"]["id"] == 1
        assert summary["last_message_direction"] == "outbound"

    def test_id_tiebreaker_orders_same_timestamp(self):
        same = _now()
        summary = compute_thread_summary([
            _brief_msg(2, "outbound", same, sender_name="Me"),
            _brief_msg(1, "inbound", same, sender_name="Sarah"),
        ])
        # Highest id wins on equal timestamps.
        assert summary["last_reply"]["id"] == 2

    def test_order_independence(self):
        msgs = [
            _brief_msg(1, "inbound", _now() - timedelta(days=2), sender_name="Sarah"),
            _brief_msg(2, "outbound", _now() - timedelta(days=1), sender_name="Me"),
            _brief_msg(3, "inbound", _now(), sender_name="Sarah"),
        ]
        forward = compute_thread_summary(msgs)
        backward = compute_thread_summary(list(reversed(msgs)))
        assert forward == backward

    def test_deterministic(self):
        msgs = [
            _brief_msg(1, "inbound", _now() - timedelta(days=2), sender_name="Sarah"),
            _brief_msg(2, "outbound", _now() - timedelta(days=1), sender_name="Me"),
        ]
        assert compute_thread_summary(msgs) == compute_thread_summary(msgs)


# ---------------------------------------------------------------------------
# Service: generation_method per creation path
# ---------------------------------------------------------------------------

class TestGenerationMethod:

    def test_manual_create_is_manual(self, db_session):
        from app.communication.schemas import CommunicationMessageCreate
        user = _create_user(db_session)
        msg = CommunicationService.create(
            db_session, user.id,
            CommunicationMessageCreate(
                message_type="follow_up", body="Hello", recipient_name="Sarah",
            ),
        )
        assert msg.generation_method == "manual"

    def test_ai_generate_is_ai_generated(self, db_session):
        user = _create_user(db_session)
        msg = CommunicationService.create_from_generation(
            db=db_session,
            user_id=user.id,
            message_type="cold_email",
            tone="professional",
            recipient_name="Sarah",
            recipient_role="Recruiter",
            recipient_company="Acme",
            subject="Intro",
            body="Hi Sarah",
        )
        assert msg.generation_method == "ai_generated"

    def test_log_inbound_is_manual(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        msg = CommunicationService.log_inbound(
            db=db_session,
            user_id=user.id,
            related_job_application_id=job.id,
            body="Pasted email",
            sender_name="Sarah",
        )
        assert msg.generation_method == "manual"

    def test_duplicate_copies_generation_method(self, db_session):
        user = _create_user(db_session)
        ai_msg = CommunicationService.create_from_generation(
            db=db_session,
            user_id=user.id,
            message_type="cold_email",
            tone="professional",
            recipient_name="Sarah",
            recipient_role=None,
            recipient_company="Acme",
            subject="Intro",
            body="Hi Sarah",
        )
        dup_ai = CommunicationService.duplicate(db_session, ai_msg.id, user.id, "Copy of Intro")
        assert dup_ai.generation_method == "ai_generated"

        manual_msg = CommunicationService.create_from_generation(
            db=db_session,
            user_id=user.id,
            message_type="follow_up",
            tone="professional",
            recipient_name="Sarah",
            recipient_role=None,
            recipient_company=None,
            subject="Check in",
            body="Following up",
            direction="inbound",
        )
        manual_msg.generation_method = "manual"
        db_session.commit()
        dup_manual = CommunicationService.duplicate(db_session, manual_msg.id, user.id, "Copy")
        assert dup_manual.generation_method == "manual"


# ---------------------------------------------------------------------------
# Service: attach_thread_summary
# ---------------------------------------------------------------------------

class TestAttachThreadSummary:

    def test_attach_full_thread_summary(self, db_session):
        from app.communication.models import CommunicationMessage
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)

        db_session.add(CommunicationMessage(
            user_id=user.id, message_type="recruiter_email", tone="professional",
            direction="inbound", body="Hi", sender_name="Sarah",
            related_job_application_id=job.id, version=1, version_history="[]",
        ))
        db_session.add(CommunicationMessage(
            user_id=user.id, message_type="recruiter_reply", tone="professional",
            direction="outbound", body="Hello", recipient_name="Sarah",
            related_job_application_id=job.id, version=1, version_history="[]",
        ))
        db_session.commit()

        thread = CommunicationService.get_thread(db_session, user.id, job.id)
        attached = attach_thread_summary(db_session, thread)
        assert len(attached) == 2
        for m in attached:
            assert m.thread_summary["has_thread"] is True
            assert m.thread_summary["state"] in (STATE_WAITING, STATE_NEEDS_REPLY)

    def test_attach_empty_slice_returns_empty(self, db_session):
        assert attach_thread_summary(db_session, []) == []


# ---------------------------------------------------------------------------
# API: thread summary + generation_method in responses
# ---------------------------------------------------------------------------

class TestThreadSummaryApi:

    @pytest.fixture
    def client(self, db_session, monkeypatch):
        class _FakeProvider:
            def generate_cold_email(self, **kwargs):
                return {"subject": "Intro", "body": "Hi Sarah"}
            def generate_recruiter_reply(self, **kwargs):
                return {"subject": "Re: Interview", "body": "Generated reply"}
        monkeypatch.setattr("app.communication.router.get_provider", lambda: _FakeProvider())

        def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def _auth(self, user):
        token = create_access_token(data={"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    def test_thread_response_carries_generation_method_and_summary(self, client, db_session):
        from app.communication.models import CommunicationMessage
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)

        db_session.add(CommunicationMessage(
            user_id=user.id, message_type="recruiter_email", tone="professional",
            direction="inbound", body="Hi", sender_name="Sarah",
            related_job_application_id=job.id, version=1, version_history="[]",
        ))
        db_session.commit()

        r = client.get(f"/api/communication/thread/{job.id}", headers=headers)
        assert r.status_code == 200
        data = r.json()[0]
        assert data["generation_method"] == "manual"
        assert data["thread_summary"]["has_thread"] is True
        assert data["thread_summary"]["state"] == STATE_NEEDS_REPLY

    def test_generate_endpoint_tags_ai_generated(self, client, db_session):
        user = _create_user(db_session)
        headers = self._auth(user)

        r = client.post("/api/communication/generate", headers=headers, json={
            "message_type": "cold_email",
            "recipient_name": "Sarah",
            "recipient_company": "Acme",
        })
        assert r.status_code == 201
        assert r.json()["generation_method"] == "ai_generated"

    def test_list_response_carries_thread_summary(self, client, db_session):
        from app.communication.models import CommunicationMessage
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)

        db_session.add(CommunicationMessage(
            user_id=user.id, message_type="follow_up", tone="professional",
            direction="outbound", body="Following up", recipient_name="Sarah",
            related_job_application_id=job.id, version=1, version_history="[]",
        ))
        db_session.commit()

        r = client.get("/api/communication", headers=headers)
        assert r.status_code == 200
        data = r.json()[0]
        assert data["thread_summary"]["has_thread"] is True
        assert data["thread_summary"]["state"] == STATE_WAITING


# ---------------------------------------------------------------------------
# API: interview sessions for an application (timeline interleave source)
# ---------------------------------------------------------------------------

class TestApplicationSessionsApi:

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

    def test_sessions_for_application_returns_practice_and_real(self, client, db_session):
        from app.interview_prep.models import InterviewSession
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)

        db_session.add(InterviewSession(
            user_id=user.id, session_type="practice", job_title="Engineer",
            question_count=5, related_job_application_id=job.id,
            overall_score=80, completed_at=datetime.utcnow(),
        ))
        db_session.add(InterviewSession(
            user_id=user.id, session_type="real_interview", job_title="Engineer",
            company_name="Acme", question_count=0, related_job_application_id=job.id,
            how_it_went="Went well", self_rated_confidence=75,
            completed_at=datetime.utcnow(),
        ))
        db_session.commit()

        r = client.get(f"/api/interview-prep/applications/{job.id}/sessions", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        types = {s["session_type"] for s in data}
        assert types == {"practice", "real_interview"}

    def test_sessions_scoped_to_application(self, client, db_session):
        from app.interview_prep.models import InterviewSession
        user = _create_user(db_session)
        job_a = _create_job_application(db_session, user.id, "Acme")
        job_b = _create_job_application(db_session, user.id, "Beta")
        headers = self._auth(user)

        db_session.add(InterviewSession(
            user_id=user.id, session_type="practice", job_title="A",
            question_count=5, related_job_application_id=job_a.id,
            overall_score=80, completed_at=datetime.utcnow(),
        ))
        db_session.add(InterviewSession(
            user_id=user.id, session_type="real_interview", job_title="B",
            question_count=0, related_job_application_id=job_b.id,
            how_it_went="Went well", self_rated_confidence=70,
            completed_at=datetime.utcnow(),
        ))
        db_session.commit()

        r = client.get(f"/api/interview-prep/applications/{job_a.id}/sessions", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["session_type"] == "practice"

    def test_sessions_foreign_application_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job_application(db_session, owner.id, "OwnerCo")

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = self._auth(attacker)

        r = client.get(f"/api/interview-prep/applications/{job.id}/sessions", headers=headers)
        assert r.status_code == 404

    def test_sessions_requires_auth(self, client):
        r = client.get("/api/interview-prep/applications/1/sessions")
        assert r.status_code == 401
