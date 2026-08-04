"""Tests for the computed skill-gap summary (real insight from stored JD matches).

Covers:
- Frequency tallying of missing_skills across JDMatchResult rows
- Ranking by occurrence count (ties broken alphabetically)
- "Not enough data" threshold behavior below the minimum sample size
- Per-user scoping (only the current user's rows are considered)
- Auth required; malformed stored JSON is skipped without breaking the tally
"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dependencies import create_access_token


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
def client(db_session):
    def _get_db_override():
        yield db_session
    app.dependency_overrides[get_db] = _get_db_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


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


def _create_job(db, user_id, company="Acme", job_title="Engineer"):
    from app.models.job_application import JobApplication
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


def _seed_match(db, user_id, missing_skill_names, job=None):
    """Create a stored JDMatchResult row with the given missing skills."""
    from app.models.jd_match_result import JDMatchResult
    items = [{"name": name, "in_jd": True, "in_resume": False} for name in missing_skill_names]
    job_id = job.id if job is not None else None
    r = JDMatchResult(
        user_id=user_id,
        job_application_id=job_id,
        resume_id=None,
        match_score=80.0,
        matched_skills=json.dumps([]),
        missing_skills=json.dumps(items),
        used_ai=False,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _auth(user):
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Service: frequency tally + threshold
# ---------------------------------------------------------------------------

class TestSkillGapSummaryService:

    def _summary(self, db_session, user_id):
        from app.career.services.analytics_service import get_skill_gap_summary
        return get_skill_gap_summary(db_session, user_id)

    def test_insufficient_data_below_minimum(self, db_session):
        user = _create_user(db_session)
        _seed_match(db_session, user.id, ["Docker"])
        _seed_match(db_session, user.id, ["Kubernetes"])

        summary = self._summary(db_session, user.id)
        assert summary["has_data"] is False
        assert summary["insufficient_data"] is True
        assert summary["total_applications"] == 2
        assert summary["top_missing_skills"] == []

    def test_zero_rows_is_insufficient(self, db_session):
        user = _create_user(db_session)
        summary = self._summary(db_session, user.id)
        assert summary["has_data"] is False
        assert summary["insufficient_data"] is True
        assert summary["total_applications"] == 0

    def test_tally_counts_frequency_across_applications(self, db_session):
        user = _create_user(db_session)
        # Docker missing in 4 applications, Kubernetes in 2, Terraform in 1.
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"])
        _seed_match(db_session, user.id, ["Docker"])
        _seed_match(db_session, user.id, ["Docker", "Terraform"])
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"])

        summary = self._summary(db_session, user.id)
        assert summary["has_data"] is True
        assert summary["total_applications"] == 4

        skills = {s["name"]: s["count"] for s in summary["top_missing_skills"]}
        assert skills["Docker"] == 4
        assert skills["Kubernetes"] == 2
        assert skills["Terraform"] == 1

    def test_ranking_by_count_then_name(self, db_session):
        user = _create_user(db_session)
        _seed_match(db_session, user.id, ["AWS"])
        _seed_match(db_session, user.id, ["AWS"])
        _seed_match(db_session, user.id, ["Docker", "AWS"])
        _seed_match(db_session, user.id, ["Zed"])

        summary = self._summary(db_session, user.id)
        names = [s["name"] for s in summary["top_missing_skills"]]
        assert names[0] == "AWS"
        # count=1 ties are alphabetical.
        assert names[1] == "Docker"
        assert names[2] == "Zed"

    def test_top_n_limits_results(self, db_session):
        user = _create_user(db_session)
        for i in range(8):
            _seed_match(db_session, user.id, [f"Skill{i}"])

        summary = self._summary(db_session, user.id)
        assert len(summary["top_missing_skills"]) == 5

    def test_malformed_stored_json_is_skipped(self, db_session):
        user = _create_user(db_session)
        from app.models.jd_match_result import JDMatchResult
        _seed_match(db_session, user.id, ["Docker"])
        _seed_match(db_session, user.id, ["Docker"])
        _seed_match(db_session, user.id, ["Kubernetes"])

        bad = JDMatchResult(
            user_id=user.id, job_application_id=None, resume_id=None,
            match_score=80.0, matched_skills="not-json",
            missing_skills="[not valid json", used_ai=False,
        )
        db_session.add(bad)
        db_session.commit()

        summary = self._summary(db_session, user.id)
        # The malformed row still counts toward the sample size but contributes
        # no skills; Docker and Kubernetes are the only tallied skills.
        assert summary["has_data"] is True
        assert summary["total_applications"] == 4
        skills = {s["name"]: s["count"] for s in summary["top_missing_skills"]}
        assert skills == {"Docker": 2, "Kubernetes": 1}

    def test_scoped_to_user(self, db_session):
        alice = _create_user(db_session, email="alice@test.com", username="alice")
        bob = _create_user(db_session, email="bob@test.com", username="bob")

        _seed_match(db_session, alice.id, ["Docker"])
        _seed_match(db_session, alice.id, ["Docker"])
        _seed_match(db_session, alice.id, ["Kubernetes"])
        _seed_match(db_session, bob.id, ["SomethingElse"])

        summary = self._summary(db_session, alice.id)
        assert summary["total_applications"] == 3
        names = [s["name"] for s in summary["top_missing_skills"]]
        assert names == ["Docker", "Kubernetes"]
        assert "SomethingElse" not in names


# ---------------------------------------------------------------------------
# API endpoint
# ---------------------------------------------------------------------------

class TestSkillGapSummaryApi:

    def test_requires_auth(self, client):
        r = client.get("/api/career/skill-gap-summary")
        assert r.status_code == 401

    def test_returns_insufficient_data_response(self, client, db_session):
        user = _create_user(db_session)
        _seed_match(db_session, user.id, ["Docker"])

        r = client.get("/api/career/skill-gap-summary", headers=_auth(user))
        assert r.status_code == 200
        data = r.json()
        assert data["has_data"] is False
        assert data["insufficient_data"] is True
        assert data["total_applications"] == 1
        assert "message" in data

    def test_returns_ranked_insight(self, client, db_session):
        user = _create_user(db_session)
        jobs = [_create_job(db_session, user.id, f"Company{i}") for i in range(4)]
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"], jobs[0])
        _seed_match(db_session, user.id, ["Docker"], jobs[1])
        _seed_match(db_session, user.id, ["Docker", "Terraform"], jobs[2])
        _seed_match(db_session, user.id, ["Kubernetes"], jobs[3])

        r = client.get("/api/career/skill-gap-summary", headers=_auth(user))
        assert r.status_code == 200
        data = r.json()
        assert data["has_data"] is True
        assert data["total_applications"] == 4

        skills = {s["name"]: s["count"] for s in data["top_missing_skills"]}
        assert skills["Docker"] == 3
        assert skills["Kubernetes"] == 2
        assert skills["Terraform"] == 1

    def test_scoped_to_current_user(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        other = _create_user(db_session, email="other@test.com", username="other")
        for _ in range(3):
            _seed_match(db_session, owner.id, ["OwnerSkill"])
        for _ in range(3):
            _seed_match(db_session, other.id, ["OtherSkill"])

        r = client.get("/api/career/skill-gap-summary", headers=_auth(owner))
        data = r.json()
        names = [s["name"] for s in data["top_missing_skills"]]
        assert names == ["OwnerSkill"]
