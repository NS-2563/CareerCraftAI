"""Tests for the deterministic resume score-history diff.

Covers:
- extract_resume_content captures skills + summary from various shapes
- compute_content_diff returns exactly the added/removed skills and summary facts
- jd_keywords_now_covered cross-references stored JD-match missing skills
- the diff endpoint returns the correct computed changes for seeded snapshots
- missing content / wrong ownership / mismatched metrics are rejected
"""

import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.analytics.models import ScoreSnapshot
from app.analytics.service import (
    AnalyticsService,
    compute_content_diff,
    extract_resume_content,
    jd_keywords_now_covered,
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
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, email="diff@test.com", username="diff_user"):
    from app.models.user import User
    from app.dependencies import get_password_hash
    u = User(email=email, username=username,
             hashed_password=get_password_hash("Test1234!"), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_resume(db, user_id):
    from app.models.resume import Resume
    r = Resume(user_id=user_id, name="Diff Resume", completed=False)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _snapshot(db, user_id, resume_id, value, skills, summary, recorded_at=None):
    snap = ScoreSnapshot(
        user_id=user_id,
        resume_id=resume_id,
        metric_type="ats_score",
        value=value,
        content_json={"skills": skills, "summary": summary},
        recorded_at=recorded_at or datetime.utcnow(),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


# ---------------------------------------------------------------------------
# Content capture
# ---------------------------------------------------------------------------

class TestContentCapture:

    def test_extracts_skills_and_summary(self):
        content = extract_resume_content({
            "skills": [{"name": "Python"}, "Docker"],
            "summary": "  Experienced backend developer.  ",
        })
        assert content == {"skills": ["Python", "Docker"], "summary": "Experienced backend developer."}

    def test_handles_skills_json_string(self):
        content = extract_resume_content({
            "skills": json.dumps([{"name": "Python"}, {"name": "Java"}]),
            "summary": "Hello",
        })
        assert content["skills"] == ["Python", "Java"]

    def test_handles_summary_under_personal(self):
        content = extract_resume_content({
            "skills": ["Python"],
            "personal": {"summary": "Nested summary"},
        })
        assert content["summary"] == "Nested summary"

    def test_none_for_non_dict(self):
        assert extract_resume_content(None) is None
        assert extract_resume_content("nope") is None

    def test_dedups_casing_variants(self):
        content = extract_resume_content({"skills": ["Python", "python"], "summary": ""})
        assert content["skills"] == ["Python"]


# ---------------------------------------------------------------------------
# Diff computation (pure)
# ---------------------------------------------------------------------------

class TestComputeDiff:

    def test_skills_added_removed_and_summary_delta(self):
        diff = compute_content_diff(
            {"skills": ["Python", "Java"], "summary": "Experienced in Python."},
            {"skills": ["Python", "Docker"], "summary": "Experienced in Python and Docker."},
        )
        assert diff["skills_added"] == ["Docker"]
        assert diff["skills_removed"] == ["Java"]
        assert diff["summary_changed"] is True
        assert diff["summary_word_delta"] == 2

    def test_no_changes(self):
        diff = compute_content_diff(
            {"skills": ["Python"], "summary": "Same"},
            {"skills": ["python"], "summary": "Same"},
        )
        assert diff["skills_added"] == []
        assert diff["skills_removed"] == []
        assert diff["summary_changed"] is False
        assert diff["summary_word_delta"] == 0

    def test_preserves_original_casing_for_added(self):
        diff = compute_content_diff(
            {"skills": ["Python"], "summary": "a"},
            {"skills": ["Python", "docker"], "summary": "a"},
        )
        assert diff["skills_added"] == ["docker"]

    def test_word_delta_negative_when_summary_shrinks(self):
        diff = compute_content_diff(
            {"skills": [], "summary": "one two three four"},
            {"skills": [], "summary": "one"},
        )
        assert diff["summary_changed"] is True
        assert diff["summary_word_delta"] == -3


# ---------------------------------------------------------------------------
# JD keyword coverage
# ---------------------------------------------------------------------------

class TestJdKeywordCoverage:

    def test_added_skills_covering_missing_jd_keywords(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        from app.models.jd_match_result import JDMatchResult
        from app.models.job_application import JobApplication
        from app.schemas.job_tracker import JobStatus
        job = JobApplication(user_id=user.id, company="Acme", job_title="Engineer",
                             status=JobStatus("Applied"))
        db_session.add(job)
        db_session.flush()
        missing = json.dumps([{"name": "Docker"}, "Kubernetes"])
        row = JDMatchResult(
            user_id=user.id, job_application_id=job.id, resume_id=resume.id,
            match_score=70.0, matched_skills=json.dumps(["Python"]),
            missing_skills=missing, used_ai=False,
        )
        db_session.add(row)
        db_session.commit()

        covered = jd_keywords_now_covered(db_session, user.id, resume.id, ["Docker", "Kubernetes", "Python"])
        assert covered == ["Docker", "Kubernetes"]

    def test_no_matches_returns_empty(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        covered = jd_keywords_now_covered(db_session, user.id, resume.id, ["Docker"])
        assert covered == []

    def test_only_own_resume_rows_considered(self, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        from app.models.jd_match_result import JDMatchResult
        row = JDMatchResult(
            user_id=user.id, resume_id=None,
            match_score=70.0, matched_skills="[]",
            missing_skills=json.dumps(["Docker"]), used_ai=False,
        )
        db_session.add(row)
        db_session.commit()
        covered = jd_keywords_now_covered(db_session, user.id, resume.id, ["Docker"])
        assert covered == []


# ---------------------------------------------------------------------------
# API: GET /api/resume/{resume_id}/score-history/diff
# ---------------------------------------------------------------------------

class TestScoreDiffApi:

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
            "email": "diff@test.com", "password": "Test1234!",
        })
        assert r.status_code == 200
        token = r.json().get("access_token", "")
        return user, {"Authorization": f"Bearer {token}"}

    def _seed_two_snapshots(self, db_session, user, resume):
        base = datetime.utcnow()
        snap_a = _snapshot(
            db_session, user.id, resume.id, 72.0,
            ["Python", "Java"],
            "Experienced backend developer in Python.",
            recorded_at=base - timedelta(days=2),
        )
        snap_b = _snapshot(
            db_session, user.id, resume.id, 85.0,
            ["Python", "Docker"],
            "Experienced backend developer in Python and Docker.",
            recorded_at=base - timedelta(hours=1),
        )
        return snap_a, snap_b

    def test_diff_returns_exact_computed_changes(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        snap_a, snap_b = self._seed_two_snapshots(db_session, user, resume)

        r = client.get(
            f"/api/resume/{resume.id}/score-history/diff"
            f"?from={snap_a.id}&to={snap_b.id}",
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["resume_id"] == resume.id
        assert data["metric_type"] == "ats_score"
        assert data["from"]["snapshot_id"] == snap_a.id
        assert data["to"]["snapshot_id"] == snap_b.id
        assert data["score_delta"] == 13.0
        assert data["content_available"] is True
        assert data["skills_added"] == ["Docker"]
        assert data["skills_removed"] == ["Java"]
        assert data["summary_changed"] is True
        assert data["summary_word_delta"] == 2

    def test_diff_reversed_swaps_roles(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        snap_a, snap_b = self._seed_two_snapshots(db_session, user, resume)

        r = client.get(
            f"/api/resume/{resume.id}/score-history/diff"
            f"?from={snap_b.id}&to={snap_a.id}",
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["skills_added"] == ["Java"]
        assert data["skills_removed"] == ["Docker"]
        assert data["score_delta"] == -13.0

    def test_diff_reports_jd_keywords_now_covered(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        snap_a, snap_b = self._seed_two_snapshots(db_session, user, resume)
        from app.models.jd_match_result import JDMatchResult
        from app.models.job_application import JobApplication
        from app.schemas.job_tracker import JobStatus
        job = JobApplication(user_id=user.id, company="Acme", job_title="Engineer",
                             status=JobStatus("Applied"))
        db_session.add(job)
        db_session.flush()
        db_session.add(JDMatchResult(
            user_id=user.id, job_application_id=job.id, resume_id=resume.id,
            match_score=70.0, matched_skills=json.dumps(["Python"]),
            missing_skills=json.dumps([{"name": "Docker"}]), used_ai=False,
        ))
        db_session.commit()

        r = client.get(
            f"/api/resume/{resume.id}/score-history/diff"
            f"?from={snap_a.id}&to={snap_b.id}",
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["jd_keywords_now_covered"] == ["Docker"]

    def test_diff_rejects_missing_content(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        snap_a = _snapshot(db_session, user.id, resume.id, 72.0, ["Python"], "x",
                           recorded_at=datetime.utcnow() - timedelta(days=2))
        snap_b = ScoreSnapshot(
            user_id=user.id, resume_id=resume.id, metric_type="ats_score",
            value=85.0, content_json=None, recorded_at=datetime.utcnow(),
        )
        db_session.add(snap_b)
        db_session.commit()

        r = client.get(
            f"/api/resume/{resume.id}/score-history/diff"
            f"?from={snap_a.id}&to={snap_b.id}",
            headers=headers,
        )
        assert r.status_code == 409

    def test_diff_rejects_snapshot_from_another_resume(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        other = _create_resume(db_session, user.id)
        snap_a = _snapshot(db_session, user.id, resume.id, 72.0, ["Python"], "x",
                           recorded_at=datetime.utcnow() - timedelta(days=2))
        snap_b = _snapshot(db_session, user.id, other.id, 85.0, ["Python"], "x",
                           recorded_at=datetime.utcnow())

        r = client.get(
            f"/api/resume/{resume.id}/score-history/diff"
            f"?from={snap_a.id}&to={snap_b.id}",
            headers=headers,
        )
        assert r.status_code == 400

    def test_diff_rejects_mismatched_metric_types(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        snap_a = _snapshot(db_session, user.id, resume.id, 72.0, ["Python"], "x",
                           recorded_at=datetime.utcnow() - timedelta(days=2))
        snap_b = ScoreSnapshot(
            user_id=user.id, resume_id=resume.id, metric_type="resume_score",
            value=85.0,
            content_json={"skills": ["Python"], "summary": "x"},
            recorded_at=datetime.utcnow(),
        )
        db_session.add(snap_b)
        db_session.commit()

        r = client.get(
            f"/api/resume/{resume.id}/score-history/diff"
            f"?from={snap_a.id}&to={snap_b.id}",
            headers=headers,
        )
        assert r.status_code == 400

    def test_diff_rejects_unknown_snapshot(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        snap = _snapshot(db_session, user.id, resume.id, 72.0, ["Python"], "x")
        r = client.get(
            f"/api/resume/{resume.id}/score-history/diff"
            f"?from={snap.id}&to=999999",
            headers=headers,
        )
        assert r.status_code == 404

    def test_diff_requires_auth(self, client, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        snap_a, snap_b = self._seed_two_snapshots(db_session, user, resume)
        r = client.get(
            f"/api/resume/{resume.id}/score-history/diff"
            f"?from={snap_a.id}&to={snap_b.id}",
        )
        assert r.status_code == 401
