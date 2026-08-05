"""Tests for Profile & Settings backend support.

Covers:
- POST /api/auth/change-password
  - correct current password succeeds and invalidates old tokens
  - incorrect current password is rejected with a generic error
  - new password minimum length is enforced
  - rate limiting engages after repeated attempts
- POST /api/auth/logout-all
  - increments token_version and invalidates previously issued tokens
  - requires authentication
- DELETE /api/user/profile
  - account deletion removes the user and cascades to related data
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import settings
from app.core.limiter import limiter
from app.database import Base, get_db
from app.dependencies import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.resume import Resume  # noqa: F401
from app.models.cover_letter import CoverLetter  # noqa: F401
from app.models.career_report import CareerReport  # noqa: F401
from app.models.job_application import JobApplication  # noqa: F401

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ─── helpers ───────────────────────────────────────────────────────────

def _create_user(db, email="ps@example.com", username="psuser", password="Current123!", user_id=None):
    user = User(
        id=user_id,
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_headers(user):
    token = create_access_token(data={"sub": str(user.id)}, token_version=user.token_version)
    return {"Authorization": f"Bearer {token}"}


def _create_resume(db, user_id, name="Test Resume"):
    from app.models.resume import Resume
    r = Resume(user_id=user_id, name=name, completed=True)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _create_cover_letter(db, user_id, title="Cover Letter"):
    from app.models.cover_letter import CoverLetter
    cl = CoverLetter(user_id=user_id, title=title)
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl


def _create_career_report(db, user_id, readiness_score=70):
    from app.models.career_report import CareerReport
    cr = CareerReport(user_id=user_id, career_goal="Software Engineer",
                      readiness_score=readiness_score, source="ai", report_json={})
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return cr


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


def _create_communication_message(db, user_id, subject="Message"):
    from app.communication.models import CommunicationMessage
    msg = CommunicationMessage(user_id=user_id, message_type="follow_up",
                                recipient_name="Recipient", subject=subject,
                                body="Test message body")
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def _create_interview_session(db, user_id, overall_score=80.0):
    from datetime import datetime, timezone
    from app.interview_prep.models import InterviewSession
    s = InterviewSession(
        user_id=user_id, job_title="Engineer", difficulty="medium",
        question_count=5, overall_score=overall_score,
        completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ─── Update profile validation ──────────────────────────────────────────

class TestUpdateProfile:

    def test_update_profile_success(self, db_session, client):
        user = _create_user(db_session, email="up_ok@example.com", username="upok",
                            password="Current123!", user_id=4001)
        resp = client.put(
            "/api/user/profile",
            json={"full_name": "Jordan Rivera", "username": "upok",
                  "email": "up_ok@example.com", "profile_picture": ""},
            headers=_auth_headers(user),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["full_name"] == "Jordan Rivera"
        assert body["username"] == "upok"

    def test_update_profile_rejects_short_username_with_detail_array(self, db_session, client):
        user = _create_user(db_session, email="up_short@example.com", username="upshort",
                            password="Current123!", user_id=4002)
        resp = client.put(
            "/api/user/profile",
            json={"username": "ab"},
            headers=_auth_headers(user),
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert isinstance(detail, list)
        assert all(isinstance(e, dict) and "msg" in e for e in detail)
        assert any("username" in str(e.get("loc", [])) for e in detail)

    def test_update_profile_rejects_empty_email(self, db_session, client):
        user = _create_user(db_session, email="up_empty@example.com", username="upempty",
                            password="Current123!", user_id=4003)
        resp = client.put(
            "/api/user/profile",
            json={"email": ""},
            headers=_auth_headers(user),
        )
        assert resp.status_code == 422

    def test_update_profile_rejects_overlong_profile_picture(self, db_session, client):
        user = _create_user(db_session, email="up_long@example.com", username="uplong",
                            password="Current123!", user_id=4004)
        resp = client.put(
            "/api/user/profile",
            json={"profile_picture": "x" * 2049},
            headers=_auth_headers(user),
        )
        assert resp.status_code == 422


# ─── Change password ───────────────────────────────────────────────────

class TestChangePassword:

    def test_change_password_success_invalidates_old_tokens(self, db_session, client):
        user = _create_user(db_session, email="cp_ok@example.com", username="cpok",
                            password="Current123!", user_id=1001)
        old_token = create_access_token(
            data={"sub": str(user.id)}, token_version=user.token_version
        )

        resp = client.post(
            "/api/auth/change-password",
            json={"current_password": "Current123!", "new_password": "NewPass123!"},
            headers={"Authorization": f"Bearer {old_token}"},
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

        db_session.refresh(user)
        assert user.token_version == 1
        assert verify_password("NewPass123!", user.hashed_password) is True
        assert verify_password("Current123!", user.hashed_password) is False

        # Old access token must no longer authenticate
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"})
        assert me.status_code == 401

    def test_change_password_wrong_current_rejected(self, db_session, client):
        user = _create_user(db_session, email="cp_wrong@example.com", username="cpwrong",
                            password="Current123!", user_id=1002)
        before = user.token_version

        resp = client.post(
            "/api/auth/change-password",
            json={"current_password": "WrongPass123!", "new_password": "NewPass123!"},
            headers=_auth_headers(user),
        )
        assert resp.status_code == 401
        body = resp.json()
        assert "incorrect" in body.get("message", "").lower()

        db_session.refresh(user)
        assert user.token_version == before
        assert verify_password("Current123!", user.hashed_password) is True

    def test_change_password_enforces_min_length(self, db_session, client):
        user = _create_user(db_session, email="cp_min@example.com", username="cpmin",
                            password="Current123!", user_id=1003)

        resp = client.post(
            "/api/auth/change-password",
            json={"current_password": "Current123!", "new_password": "short"},
            headers=_auth_headers(user),
        )
        assert resp.status_code == 422

    def test_change_password_requires_auth(self, db_session, client):
        resp = client.post(
            "/api/auth/change-password",
            json={"current_password": "Current123!", "new_password": "NewPass123!"},
        )
        assert resp.status_code == 401

    def test_change_password_rate_limited(self, db_session, client):
        user = _create_user(db_session, email="cp_rl@example.com", username="cprl",
                            password="Current123!", user_id=989001)

        # This test deliberately verifies 429 enforcement, so it opts back in to
        # the limiter that the rest of the suite runs with disabled.
        limiter.enabled = True
        try:
            last_resp = None
            for _ in range(8):
                last_resp = client.post(
                    "/api/auth/change-password",
                    json={"current_password": "WrongPass123!", "new_password": "NewPass123!"},
                    headers=_auth_headers(user),
                )
                if last_resp.status_code == 429:
                    break

            assert last_resp is not None and last_resp.status_code == 429, (
                f"Expected eventual 429, last status: {last_resp.status_code if last_resp else 'N/A'}"
            )
        finally:
            limiter.enabled = not settings.TESTING


# ─── Logout all devices ────────────────────────────────────────────────

class TestLogoutAll:

    def test_logout_all_increments_version_and_invalidates_tokens(self, db_session, client):
        user = _create_user(db_session, email="loa@example.com", username="loauser",
                            password="Current123!", user_id=2001)
        old_token = create_access_token(
            data={"sub": str(user.id)}, token_version=user.token_version
        )

        resp = client.post("/api/auth/logout-all", headers={"Authorization": f"Bearer {old_token}"})
        assert resp.status_code == 200

        db_session.refresh(user)
        assert user.token_version == 1

        # Previously issued token is now revoked
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"})
        assert me.status_code == 401

    def test_logout_all_requires_auth(self, db_session, client):
        resp = client.post("/api/auth/logout-all")
        assert resp.status_code == 401


# ─── Account deletion cascade ──────────────────────────────────────────

class TestAccountDeletion:

    def test_delete_account_removes_user_and_cascades(self, db_session, client):
        user = _create_user(db_session, email="del@example.com", username="deluser",
                            password="Current123!", user_id=3001)
        user_id = user.id
        _create_resume(db_session, user_id)
        _create_cover_letter(db_session, user_id)
        _create_career_report(db_session, user_id)
        _create_job_application(db_session, user_id)
        _create_communication_message(db_session, user_id)
        _create_interview_session(db_session, user_id)

        assert db_session.query(User).count() == 1

        resp = client.delete("/api/user/profile", headers=_auth_headers(user))
        assert resp.status_code == 200

        assert db_session.query(User).filter(User.id == user_id).first() is None
        assert db_session.query(Resume).filter(Resume.user_id == user_id).count() == 0
        assert db_session.query(CoverLetter).filter(CoverLetter.user_id == user_id).count() == 0
        assert db_session.query(CareerReport).filter(CareerReport.user_id == user_id).count() == 0
        assert db_session.query(JobApplication).filter(JobApplication.user_id == user_id).count() == 0
        from app.communication.models import CommunicationMessage
        from app.interview_prep.models import InterviewSession
        assert db_session.query(CommunicationMessage).filter(
            CommunicationMessage.user_id == user_id).count() == 0
        assert db_session.query(InterviewSession).filter(
            InterviewSession.user_id == user_id).count() == 0
