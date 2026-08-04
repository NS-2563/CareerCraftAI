"""Tests for per-application conversation status (Needs Reply / Waiting / Closed).

Covers:
- Deterministic derivation from last-message direction
- Auto-close on terminal application status, and the precedence rule:
  TERMINAL APPLICATION STATUS > MANUAL OVERRIDE > DERIVED
- Manual override persistence (mark closed / reopen) across further changes
- Message list/thread enrichment with the linked application's status
- Ownership scoping (IDOR) on the new endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dependencies import create_access_token
from app.communication.service import CommunicationService
from app.communication.conversation_status import (
    NEEDS_REPLY,
    WAITING,
    CLOSED,
    resolve_status,
    derive_from_direction,
    SOURCE_APPLICATION_STATUS,
    SOURCE_MANUAL,
    SOURCE_DERIVED,
    SOURCE_NONE,
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


def _create_job_application(db, user_id, company="Acme", job_title="Engineer", status="Applied"):
    from app.models.job_application import JobApplication
    from app.schemas.job_tracker import JobStatus
    j = JobApplication(
        user_id=user_id, company=company, job_title=job_title,
        status=JobStatus(status),
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def _create_message(db, user_id, job_id, direction, body="msg"):
    from app.communication.models import CommunicationMessage
    m = CommunicationMessage(
        user_id=user_id, message_type="recruiter_email" if direction == "inbound" else "follow_up",
        tone="professional", direction=direction, body=body,
        related_job_application_id=job_id,
        version=1, version_history="[]",
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def _set_app_status(db, job, status):
    from app.schemas.job_tracker import JobStatus
    job.status = JobStatus(status)
    db.commit()
    db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# Unit: derivation + precedence rule
# ---------------------------------------------------------------------------

class TestDerivation:

    def test_inbound_last_message_is_needs_reply(self):
        assert derive_from_direction("inbound") == NEEDS_REPLY

    def test_outbound_last_message_is_waiting(self):
        assert derive_from_direction("outbound") == WAITING

    def test_no_direction_derives_none(self):
        assert derive_from_direction(None) is None

    def test_derived_inbound(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        last = _create_message(db_session, user.id, job.id, "inbound")
        status, source = resolve_status(job, last)
        assert status == NEEDS_REPLY
        assert source == SOURCE_DERIVED

    def test_derived_outbound(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        last = _create_message(db_session, user.id, job.id, "outbound")
        status, source = resolve_status(job, last)
        assert status == WAITING
        assert source == SOURCE_DERIVED

    def test_no_messages_has_no_status(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        status, source = resolve_status(job, None)
        assert status is None
        assert source == SOURCE_NONE


class TestPrecedenceRule:

    def test_manual_closed_wins_over_inbound_last(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        job.conversation_status_override = CLOSED
        last = _create_message(db_session, user.id, job.id, "inbound")
        status, source = resolve_status(job, last)
        assert status == CLOSED
        assert source == SOURCE_MANUAL

    def test_manual_needs_reply_wins_over_outbound_last(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        job.conversation_status_override = NEEDS_REPLY
        last = _create_message(db_session, user.id, job.id, "outbound")
        status, source = resolve_status(job, last)
        assert status == NEEDS_REPLY
        assert source == SOURCE_MANUAL

    def test_terminal_rejected_overrides_manual_needs_reply(self, db_session):
        """THE DECIDED PRECEDENCE RULE:
        an application moving to Rejected overrides a manually-set 'needs_reply'
        — the conversation is closed because the application is over.
        """
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        job.conversation_status_override = NEEDS_REPLY
        _set_app_status(db_session, job, "Rejected")
        last = _create_message(db_session, user.id, job.id, "inbound")
        status, source = resolve_status(job, last)
        assert status == CLOSED
        assert source == SOURCE_APPLICATION_STATUS

    def test_terminal_withdrawn_overrides_manual_closed(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        job.conversation_status_override = NEEDS_REPLY
        _set_app_status(db_session, job, "Withdrawn")
        last = _create_message(db_session, user.id, job.id, "inbound")
        status, source = resolve_status(job, last)
        assert status == CLOSED

    def test_terminal_accepted_is_closed_without_messages(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id, status="Accepted")
        status, source = resolve_status(job, None)
        assert status == CLOSED
        assert source == SOURCE_APPLICATION_STATUS

    def test_offer_is_not_terminal(self, db_session):
        """Offer keeps the conversation open — negotiation may be ongoing."""
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id, status="Offer")
        last = _create_message(db_session, user.id, job.id, "inbound")
        status, _ = resolve_status(job, last)
        assert status == NEEDS_REPLY

    def test_manual_override_restored_after_app_reopened(self, db_session):
        """The stored override survives a terminal state and is restored when
        the application moves back to a non-terminal status."""
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        job.conversation_status_override = NEEDS_REPLY
        last = _create_message(db_session, user.id, job.id, "outbound")
        assert resolve_status(job, last)[0] == NEEDS_REPLY

        _set_app_status(db_session, job, "Rejected")
        assert resolve_status(job, last)[0] == CLOSED

        _set_app_status(db_session, job, "Applied")
        assert resolve_status(job, last)[0] == NEEDS_REPLY

    def test_invalid_override_value_is_ignored(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        job.conversation_status_override = "bogus"
        last = _create_message(db_session, user.id, job.id, "inbound")
        status, source = resolve_status(job, last)
        assert status == NEEDS_REPLY
        assert source == SOURCE_DERIVED


# ---------------------------------------------------------------------------
# Service: flips as messages/status change
# ---------------------------------------------------------------------------

class TestConversationStatusService:

    def test_status_flips_when_new_inbound_message_arrives(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "outbound")
        assert CommunicationService.get_conversation_status(db_session, user.id, job.id)["status"] == WAITING

        _create_message(db_session, user.id, job.id, "inbound")
        assert CommunicationService.get_conversation_status(db_session, user.id, job.id)["status"] == NEEDS_REPLY

        _create_message(db_session, user.id, job.id, "outbound")
        assert CommunicationService.get_conversation_status(db_session, user.id, job.id)["status"] == WAITING

    def test_manual_override_persists_across_new_messages(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "inbound")

        response = CommunicationService.set_conversation_status(db_session, user.id, job.id, CLOSED)
        assert response["status"] == CLOSED
        assert response["source"] == SOURCE_MANUAL

        _create_message(db_session, user.id, job.id, "inbound")
        assert CommunicationService.get_conversation_status(db_session, user.id, job.id)["status"] == CLOSED

    def test_clearing_override_reverts_to_derived(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "inbound")

        CommunicationService.set_conversation_status(db_session, user.id, job.id, CLOSED)
        assert CommunicationService.get_conversation_status(db_session, user.id, job.id)["status"] == CLOSED

        response = CommunicationService.set_conversation_status(db_session, user.id, job.id, None)
        assert response["status"] == NEEDS_REPLY
        assert response["source"] == SOURCE_DERIVED

    def test_terminal_status_closes_even_with_override(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "inbound")
        CommunicationService.set_conversation_status(db_session, user.id, job.id, NEEDS_REPLY)

        _set_app_status(db_session, job, "Rejected")
        response = CommunicationService.get_conversation_status(db_session, user.id, job.id)
        assert response["status"] == CLOSED
        assert response["source"] == SOURCE_APPLICATION_STATUS

    def test_foreign_application_raises_not_found(self, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job_application(db_session, owner.id, "OwnerCo")
        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")

        from app.utils.exceptions import NotFoundException
        with pytest.raises(NotFoundException):
            CommunicationService.get_conversation_status(db_session, attacker.id, job.id)

    def test_all_statuses_cross_application(self, db_session):
        user = _create_user(db_session)
        job_a = _create_job_application(db_session, user.id, "Acme", "Engineer")
        _create_message(db_session, user.id, job_a.id, "inbound")
        job_b = _create_job_application(db_session, user.id, "Beta", "Designer", status="Rejected")
        _create_message(db_session, user.id, job_b.id, "outbound")

        statuses = {
            row["job_application_id"]: row["status"]
            for row in CommunicationService.get_all_conversation_statuses(db_session, user.id)
        }
        assert statuses[job_a.id] == NEEDS_REPLY
        assert statuses[job_b.id] == CLOSED

    def test_attach_conversation_status_enriches_messages(self, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "outbound")
        _create_message(db_session, user.id, job.id, "inbound")

        messages = CommunicationService.get_thread(db_session, user.id, job.id)
        messages = CommunicationService.attach_conversation_status(db_session, messages)

        assert messages[-1].conversation_status == NEEDS_REPLY
        assert messages[-1].conversation_status_source == SOURCE_DERIVED
        assert messages[0].conversation_status == NEEDS_REPLY


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class TestConversationStatusApi:

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

    def test_get_status_requires_auth(self, client):
        assert client.get("/api/communication/conversation-status/1").status_code == 401

    def test_get_status_returns_derived(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "inbound")
        headers = self._auth(user)

        r = client.get(f"/api/communication/conversation-status/{job.id}", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == NEEDS_REPLY
        assert data["source"] == SOURCE_DERIVED
        assert data["last_message_direction"] == "inbound"

    def test_put_override_and_persist(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "inbound")
        headers = self._auth(user)

        r = client.put(f"/api/communication/conversation-status/{job.id}", headers=headers, json={"status": "closed"})
        assert r.status_code == 200
        assert r.json()["status"] == CLOSED
        assert r.json()["source"] == SOURCE_MANUAL

        # Stored in DB, persists across a fresh status read.
        job.conversation_status_override == CLOSED
        r2 = client.get(f"/api/communication/conversation-status/{job.id}", headers=headers)
        assert r2.json()["status"] == CLOSED

    def test_put_null_clears_override(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "inbound")
        headers = self._auth(user)

        client.put(f"/api/communication/conversation-status/{job.id}", headers=headers, json={"status": "closed"})
        r = client.put(f"/api/communication/conversation-status/{job.id}", headers=headers, json={"status": None})
        assert r.status_code == 200
        assert r.json()["status"] == NEEDS_REPLY
        assert r.json()["source"] == SOURCE_DERIVED

    def test_put_invalid_status_rejected(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        headers = self._auth(user)
        r = client.put(f"/api/communication/conversation-status/{job.id}", headers=headers, json={"status": "bogus"})
        assert r.status_code == 422

    def test_status_foreign_application_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job_application(db_session, owner.id, "OwnerCo")
        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = self._auth(attacker)

        assert client.get(f"/api/communication/conversation-status/{job.id}", headers=headers).status_code == 404
        assert client.put(
            f"/api/communication/conversation-status/{job.id}", headers=headers, json={"status": "closed"}
        ).status_code == 404

    def test_statuses_list_requires_auth(self, client):
        assert client.get("/api/communication/conversation-statuses").status_code == 401

    def test_statuses_list_scoped_to_user(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job_application(db_session, owner.id, "OwnerCo")
        _create_message(db_session, owner.id, job.id, "inbound")

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        attacker_job = _create_job_application(db_session, attacker.id, "AttackerCo")
        _create_message(db_session, attacker.id, attacker_job.id, "outbound")

        headers = self._auth(owner)
        r = client.get("/api/communication/conversation-statuses", headers=headers)
        assert r.status_code == 200
        rows = r.json()
        ids = {row["job_application_id"] for row in rows}
        assert job.id in ids
        assert attacker_job.id not in ids

    def test_message_list_includes_conversation_status(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "inbound")
        headers = self._auth(user)

        r = client.get("/api/communication", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data[0]["conversation_status"] == NEEDS_REPLY
        assert data[0]["conversation_status_source"] == SOURCE_DERIVED

    def test_thread_includes_conversation_status(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job_application(db_session, user.id)
        _create_message(db_session, user.id, job.id, "outbound")
        headers = self._auth(user)

        r = client.get(f"/api/communication/thread/{job.id}", headers=headers)
        assert r.status_code == 200
        assert r.json()[0]["conversation_status"] == WAITING
