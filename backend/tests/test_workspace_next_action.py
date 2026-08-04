"""Tests for the deterministic workspace next-action + dismissible insight cards.

Covers:
- Every branch of the next-action decision tree with seeded completion states
  (and determinism: identical state -> identical recommendation)
- Insight card derivation (JD match gaps, resume suggestions)
- Insight dismissal persistence (a dismissed card does not reappear)
- Ownership scoping (IDOR) on the new endpoints
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dependencies import create_access_token
from app.job_tracker.next_action import (
    recommend_next_action,
    FOLLOW_UP_AFTER_DAYS,
)
from app.job_tracker.workspace import (
    build_insight_cards,
    dismiss_insight,
    get_dismissed_keys,
    build_workspace_payload,
    INSIGHT_JD_MATCH_GAPS,
    INSIGHT_RESUME_SUGGESTIONS,
)
from app.models.insight_dismissal import InsightDismissal
from app.services.jd_match_result_service import persist_match_result


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


def _create_resume(db, user_id, name="Resume A"):
    from app.models.resume import Resume
    r = Resume(user_id=user_id, name=name, personal="{}", version=1)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _create_job(
    db, user_id, company="Acme", job_title="Engineer", status="Wishlist",
    job_description=None, resume_id=None, applied_date=None,
):
    from app.models.job_application import JobApplication
    from app.schemas.job_tracker import JobStatus
    j = JobApplication(
        user_id=user_id, company=company, job_title=job_title,
        status=JobStatus(status),
        job_description=job_description,
        resume_id=resume_id,
        applied_date=applied_date,
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def _create_cover_letter(db, user_id, job_id):
    from app.models.cover_letter import CoverLetter
    cl = CoverLetter(
        user_id=user_id, job_application_id=job_id, title="Letter",
        content="Hello", version=1, version_history="[]",
    )
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl


def _create_message(db, user_id, job_id, direction="outbound"):
    from app.communication.models import CommunicationMessage
    m = CommunicationMessage(
        user_id=user_id, message_type="follow_up", tone="professional",
        direction=direction, body="msg", related_job_application_id=job_id,
        version=1, version_history="[]",
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def _create_interview(db, user_id, job_id, session_type="real_interview"):
    from app.interview_prep.models import InterviewSession
    s = InterviewSession(
        user_id=user_id, session_type=session_type,
        related_job_application_id=job_id, question_count=5,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _save_match(db, user_id, job_id, resume_id, missing_skills):
    persist_match_result(
        db=db, user_id=user_id, job_application_id=job_id, resume_id=resume_id,
        result={
            "overall_match_score": 60,
            "matched_skills": [{"name": "Python", "category": "languages"}],
            "missing_skills": [{"name": s, "category": ""} for s in missing_skills],
        },
        enable_ai=False,
    )


def _save_analysis(db, user_id, resume_id, suggestions):
    from app.models.resume_analysis import ResumeAnalysis
    rec = ResumeAnalysis(
        user_id=user_id, resume_id=resume_id, resume_version=1, source="ai",
        analysis_json={"suggestions": suggestions}, scores_json={}, is_stale=0,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def _days(n):
    return (date.today() - timedelta(days=n))


# A state where every readiness step is done — individual tests remove the one
# piece they are probing.
def _state(**overrides):
    base = {
        "status": "Applied",
        "has_job_description": True,
        "has_resume": True,
        "has_jd_match": True,
        "has_cover_letter": True,
        "has_communication": True,
        "has_interview_activity": True,
        "days_since_applied": 3,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Unit: decision tree — every branch, seeded completion states
# ---------------------------------------------------------------------------

class TestDecisionTree:

    def test_terminal_accepted_is_none(self):
        assert recommend_next_action(_state(status="Accepted")) is None

    def test_terminal_rejected_is_none(self):
        assert recommend_next_action(_state(status="Rejected")) is None

    def test_terminal_withdrawn_is_none(self):
        assert recommend_next_action(_state(status="Withdrawn")) is None

    def test_terminal_wins_over_missing_everything(self):
        # Even a totally empty application is "no action" once closed.
        assert recommend_next_action(_state(status="Rejected", has_job_description=False)) is None

    def test_no_job_description(self):
        a = recommend_next_action(_state(has_job_description=False))
        assert a["key"] == "save_job_description"
        assert a["tab"] == "jd-match"

    def test_no_job_description_wins_over_other_gaps(self):
        a = recommend_next_action(_state(has_job_description=False, has_resume=False))
        assert a["key"] == "save_job_description"

    def test_no_resume(self):
        a = recommend_next_action(_state(has_resume=False))
        assert a["key"] == "link_resume"
        assert a["tab"] == "resume"

    def test_no_jd_match(self):
        a = recommend_next_action(_state(has_jd_match=False))
        assert a["key"] == "run_jd_match"
        assert a["tab"] == "jd-match"

    def test_no_cover_letter(self):
        a = recommend_next_action(_state(has_cover_letter=False))
        assert a["key"] == "generate_cover_letter"
        assert a["tab"] == "cover-letter"

    def test_follow_up_after_threshold(self):
        a = recommend_next_action(
            _state(has_communication=False, days_since_applied=FOLLOW_UP_AFTER_DAYS + 1)
        )
        assert a["key"] == "send_follow_up"
        assert a["tab"] == "communication"

    def test_no_follow_up_at_exactly_threshold(self):
        # Rule requires strictly more than N days.
        assert recommend_next_action(
            _state(has_communication=False, days_since_applied=FOLLOW_UP_AFTER_DAYS)
        ) is None

    def test_no_follow_up_below_threshold(self):
        assert recommend_next_action(
            _state(has_communication=False, days_since_applied=3)
        ) is None

    def test_no_follow_up_when_date_unknown(self):
        assert recommend_next_action(
            _state(has_communication=False, days_since_applied=None)
        ) is None

    def test_no_follow_up_when_not_active_pursuit(self):
        # Wishlist means "not applied yet" — a follow-up makes no sense.
        assert recommend_next_action(
            _state(status="Wishlist", has_communication=False, days_since_applied=20)
        ) is None

    def test_no_follow_up_when_communication_exists(self):
        assert recommend_next_action(
            _state(has_communication=True, days_since_applied=20)
        ) is None

    def test_practice_when_interview_scheduled_and_no_activity(self):
        a = recommend_next_action(
            _state(status="Interview", has_interview_activity=False)
        )
        assert a["key"] == "practice_interview"
        assert a["tab"] == "interview"

    def test_practice_when_interview_scheduled_status(self):
        a = recommend_next_action(
            _state(status="Interview", has_interview_activity=False)
        )
        assert a["key"] == "practice_interview"

    def test_no_practice_when_interview_activity_exists(self):
        assert recommend_next_action(
            _state(status="Interview", has_interview_activity=True)
        ) is None

    def test_no_practice_when_status_not_interview(self):
        # Not in an interview state -> the practice rule does not fire.
        assert recommend_next_action(
            _state(status="Applied", has_interview_activity=False)
        ) is None

    def test_all_complete_is_none(self):
        assert recommend_next_action(_state()) is None

    def test_deterministic(self):
        s = _state(status="Interview", has_interview_activity=False)
        first = recommend_next_action(s)
        second = recommend_next_action(dict(s))
        assert first == second


# ---------------------------------------------------------------------------
# Service: insight cards + dismissal persistence
# ---------------------------------------------------------------------------

class TestWorkspaceInsightsService:

    def test_jd_gap_card_when_missing_skills(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        job = _create_job(db_session, user.id, job_description="JD", resume_id=resume.id)
        _save_match(db_session, user.id, job.id, resume.id, ["Docker", "Kubernetes"])

        cards = build_insight_cards(db_session, user.id, job)
        keys = [c["key"] for c in cards]
        assert INSIGHT_JD_MATCH_GAPS in keys
        gap = next(c for c in cards if c["key"] == INSIGHT_JD_MATCH_GAPS)
        assert gap["reasons"] == ["Docker", "Kubernetes"]
        assert gap["extra_count"] == 0

    def test_no_jd_gap_card_without_missing_skills(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        job = _create_job(db_session, user.id, job_description="JD", resume_id=resume.id)
        _save_match(db_session, user.id, job.id, resume.id, [])

        cards = build_insight_cards(db_session, user.id, job)
        assert all(c["key"] != INSIGHT_JD_MATCH_GAPS for c in cards)

    def test_no_jd_gap_card_without_match(self, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id, job_description="JD")
        cards = build_insight_cards(db_session, user.id, job)
        assert cards == []

    def test_reason_cap(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        job = _create_job(db_session, user.id, job_description="JD", resume_id=resume.id)
        skills = [f"skill-{i}" for i in range(12)]
        _save_match(db_session, user.id, job.id, resume.id, skills)

        gap = next(c for c in build_insight_cards(db_session, user.id, job)
                   if c["key"] == INSIGHT_JD_MATCH_GAPS)
        assert len(gap["reasons"]) == 6
        assert gap["extra_count"] == 6

    def test_resume_suggestions_card(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        _save_analysis(db_session, user.id, resume.id, ["Add metrics", "Rewrite summary"])
        job = _create_job(db_session, user.id, resume_id=resume.id)

        cards = build_insight_cards(db_session, user.id, job)
        sug = next(c for c in cards if c["key"] == INSIGHT_RESUME_SUGGESTIONS)
        assert sug["reasons"] == ["Add metrics", "Rewrite summary"]

    def test_no_resume_suggestions_card_without_analysis(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        job = _create_job(db_session, user.id, resume_id=resume.id)
        cards = build_insight_cards(db_session, user.id, job)
        assert all(c["key"] != INSIGHT_RESUME_SUGGESTIONS for c in cards)

    def test_dismiss_persists_and_filters(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        _save_analysis(db_session, user.id, resume.id, ["Add metrics"])
        job = _create_job(db_session, user.id, resume_id=resume.id)

        assert get_dismissed_keys(db_session, user.id, job.id) == []
        assert any(c["key"] == INSIGHT_RESUME_SUGGESTIONS
                   for c in build_insight_cards(db_session, user.id, job))

        dismissed = dismiss_insight(db_session, user.id, job.id, INSIGHT_RESUME_SUGGESTIONS)
        assert INSIGHT_RESUME_SUGGESTIONS in dismissed

        # Card must not reappear via the payload (which filters dismissed keys).
        payload = build_workspace_payload(db_session, user.id, job)
        assert all(c["key"] != INSIGHT_RESUME_SUGGESTIONS for c in payload["insights"])
        assert INSIGHT_RESUME_SUGGESTIONS in payload["dismissed"]

    def test_dismiss_is_idempotent(self, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        dismiss_insight(db_session, user.id, job.id, INSIGHT_JD_MATCH_GAPS)
        second = dismiss_insight(db_session, user.id, job.id, INSIGHT_JD_MATCH_GAPS)
        assert second.count(INSIGHT_JD_MATCH_GAPS) == 1

    def test_dismissal_scoped_per_application(self, db_session):
        user = _create_user(db_session)
        job_a = _create_job(db_session, user.id, "Acme")
        job_b = _create_job(db_session, user.id, "Beta")
        dismiss_insight(db_session, user.id, job_a.id, INSIGHT_JD_MATCH_GAPS)
        assert INSIGHT_JD_MATCH_GAPS not in get_dismissed_keys(db_session, user.id, job_b.id)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class TestWorkspaceApi:

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

    def test_workspace_requires_auth(self, client):
        assert client.get("/api/jobs/1/workspace").status_code == 401

    def test_bare_job_recommends_save_jd(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        r = client.get(f"/api/jobs/{job.id}/workspace", headers=self._auth(user))
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["next_action"]["key"] == "save_job_description"
        assert data["insights"] == []

    def test_full_completion_has_no_next_action(self, client, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        job = _create_job(
            db_session, user.id, status="Applied", job_description="JD",
            resume_id=resume.id, applied_date=_days(2),
        )
        _save_match(db_session, user.id, job.id, resume.id, ["Kafka"])
        _create_cover_letter(db_session, user.id, job.id)
        _create_message(db_session, user.id, job.id)
        _create_interview(db_session, user.id, job.id, session_type="real_interview")

        r = client.get(f"/api/jobs/{job.id}/workspace", headers=self._auth(user))
        data = r.json()["data"]
        assert data["next_action"] is None

    def test_interview_status_recommends_practice(self, client, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        job = _create_job(
            db_session, user.id, status="Interview", job_description="JD",
            resume_id=resume.id,
        )
        _save_match(db_session, user.id, job.id, resume.id, [])
        _create_cover_letter(db_session, user.id, job.id)
        _create_message(db_session, user.id, job.id)

        r = client.get(f"/api/jobs/{job.id}/workspace", headers=self._auth(user))
        data = r.json()["data"]
        assert data["next_action"]["key"] == "practice_interview"

    def test_insight_present_then_dismissed_does_not_reappear(self, client, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        job = _create_job(db_session, user.id, job_description="JD", resume_id=resume.id)
        _save_match(db_session, user.id, job.id, resume.id, ["Terraform"])
        headers = self._auth(user)

        first = client.get(f"/api/jobs/{job.id}/workspace", headers=headers).json()["data"]
        assert any(c["key"] == INSIGHT_JD_MATCH_GAPS for c in first["insights"])

        post = client.post(
            f"/api/jobs/{job.id}/workspace/insights/{INSIGHT_JD_MATCH_GAPS}/dismiss",
            headers=headers,
        )
        assert post.status_code == 200
        assert INSIGHT_JD_MATCH_GAPS in post.json()["data"]["dismissed"]

        # Second visit: the card is gone (dismissal persisted, not session-only).
        second = client.get(f"/api/jobs/{job.id}/workspace", headers=headers).json()["data"]
        assert all(c["key"] != INSIGHT_JD_MATCH_GAPS for c in second["insights"])
        assert INSIGHT_JD_MATCH_GAPS in second["dismissed"]

    def test_foreign_application_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job(db_session, owner.id, "OwnerCo", job_description="JD")
        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = self._auth(attacker)

        assert client.get(f"/api/jobs/{job.id}/workspace", headers=headers).status_code == 404
        assert client.post(
            f"/api/jobs/{job.id}/workspace/insights/{INSIGHT_JD_MATCH_GAPS}/dismiss",
            headers=headers,
        ).status_code == 404

    def test_dismiss_requires_auth(self, client):
        assert client.post(
            "/api/jobs/1/workspace/insights/jd_match_gaps/dismiss"
        ).status_code == 401
