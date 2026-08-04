"""Tests for per-resume ATS/resume score history (Phase 10).

Covers:
  - ScoreSnapshot.resume_id persistence and per-resume dedup scoping
  - AnalyticsService.get_history resume_id filtering
  - the _record_score_snapshots helper (records both metrics, respects analysis_failed)
  - GET /api/resume/{resume_id}/score-history API (auth, ownership, response shape)
"""

import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.analytics.models import ScoreSnapshot
from app.analytics.service import AnalyticsService
from app.routers.analysis import _record_score_snapshots


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


def _create_user(db, email, username):
    from app.dependencies import get_password_hash
    from app.models.user import User
    u = User(email=email, username=username,
             hashed_password=get_password_hash("Test1234!"), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_resume(db, user_id, name="Resume A"):
    from app.models.resume import Resume
    r = Resume(
        user_id=user_id, name=name, completed=True,
        personal=json.dumps({"first_name": "John", "last_name": "Doe"}),
        summary="Senior engineer",
        experience=json.dumps([
            {"company": "TechCorp", "position": "Eng", "description": "Python work."},
        ]),
        skills=json.dumps([{"name": "Python", "category": "Lang"}]),
        education=json.dumps([]),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


# ---------------------------------------------------------------------------
# Unit: service resume_id scoping
# ---------------------------------------------------------------------------

class TestSnapshotResumeScoping:

    def test_record_snapshot_stores_resume_id(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=75.0, resume_id=7,
        )
        snapshots = db_session.query(ScoreSnapshot).all()
        assert len(snapshots) == 1
        assert snapshots[0].resume_id == 7

    def test_dedup_scoped_per_resume(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0, resume_id=1,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0, resume_id=1,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0, resume_id=2,
        )
        count = db_session.query(ScoreSnapshot).count()
        assert count == 2

    def test_user_level_snapshot_does_not_dedup_against_resume_snapshot(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0, resume_id=1,
        )
        count = db_session.query(ScoreSnapshot).count()
        assert count == 2

    def test_get_history_filters_by_resume_id(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=60.0, resume_id=1,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=70.0, resume_id=1,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=90.0, resume_id=2,
        )
        history = AnalyticsService.get_history(
            db_session, user_id=1, metric_type="ats_score", resume_id=1,
        )
        values = [s.value for s in history]
        assert values == [60.0, 70.0]

    def test_get_history_orders_oldest_first(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=50.0, resume_id=1,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0, resume_id=1,
        )
        history = AnalyticsService.get_history(
            db_session, user_id=1, metric_type="ats_score", resume_id=1,
        )
        assert [s.value for s in history] == [50.0, 80.0]


# ---------------------------------------------------------------------------
# Unit: _record_score_snapshots helper
# ---------------------------------------------------------------------------

class TestRecordScoreSnapshotsHelper:

    def test_records_both_metrics_with_resume_id(self, db_session):
        result = {"deterministic": {}}
        scores = {"ats_score": 68.0, "quality_score": 72.0}
        _record_score_snapshots(db_session, user_id=1, resume_id=3, result=result, scores=scores)
        snapshots = db_session.query(ScoreSnapshot).all()
        assert len(snapshots) == 2
        by_metric = {s.metric_type: s for s in snapshots}
        assert by_metric["ats_score"].value == 68.0
        assert by_metric["ats_score"].resume_id == 3
        assert by_metric["resume_score"].value == 72.0
        assert by_metric["resume_score"].resume_id == 3

    def test_skips_when_analysis_failed(self, db_session):
        result = {"analysis_failed": True, "ats_score": None}
        scores = {"ats_score": 0, "quality_score": 0}
        _record_score_snapshots(db_session, user_id=1, resume_id=3, result=result, scores=scores)
        assert db_session.query(ScoreSnapshot).count() == 0

    def test_skips_when_scores_missing(self, db_session):
        result = {"deterministic": {}}
        scores = {}
        _record_score_snapshots(db_session, user_id=1, resume_id=3, result=result, scores=scores)
        assert db_session.query(ScoreSnapshot).count() == 0


# ---------------------------------------------------------------------------
# API: GET /api/resume/{resume_id}/score-history
# ---------------------------------------------------------------------------

class TestScoreHistoryApi:

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
        user = _create_user(db_session, "scorehist@test.com", "scorehist")
        r = client.post("/api/auth/login", json={
            "email": "scorehist@test.com", "password": "Test1234!",
        })
        assert r.status_code == 200
        token = r.json().get("access_token", "")
        return user, {"Authorization": f"Bearer {token}"}

    def test_requires_auth(self, client):
        r = client.get("/api/resume/1/score-history")
        assert r.status_code == 401

    def test_empty_history(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        r = client.get(f"/api/resume/{resume.id}/score-history", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 0
        assert data["latest"] is None
        assert data["previous"] is None
        assert data["change"] is None

    def test_returns_history_oldest_first_with_delta(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        AnalyticsService.record_snapshot(
            db_session, user.id, "ats_score", 68.0, resume_id=resume.id,
        )
        AnalyticsService.record_snapshot(
            db_session, user.id, "ats_score", 75.0, resume_id=resume.id,
        )
        r = client.get(f"/api/resume/{resume.id}/score-history", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["metric_type"] == "ats_score"
        assert [s["value"] for s in data["snapshots"]] == [68.0, 75.0]
        assert data["count"] == 2
        assert data["latest"] == 75.0
        assert data["previous"] == 68.0
        assert data["change"] == 7.0

    def test_scoped_to_resume_not_other_resumes(self, client, test_user, db_session):
        user, headers = test_user
        resume_a = _create_resume(db_session, user.id, name="Resume A")
        resume_b = _create_resume(db_session, user.id, name="Resume B")
        AnalyticsService.record_snapshot(
            db_session, user.id, "ats_score", 80.0, resume_id=resume_a.id,
        )
        AnalyticsService.record_snapshot(
            db_session, user.id, "ats_score", 50.0, resume_id=resume_b.id,
        )
        r = client.get(f"/api/resume/{resume_a.id}/score-history", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert data["latest"] == 80.0

    def test_resume_score_metric(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        AnalyticsService.record_snapshot(
            db_session, user.id, "resume_score", 72.0, resume_id=resume.id,
        )
        r = client.get(
            f"/api/resume/{resume.id}/score-history?metric_type=resume_score",
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["metric_type"] == "resume_score"
        assert data["count"] == 1
        assert data["latest"] == 72.0

    def test_other_user_resume_returns_404(self, client, test_user, db_session):
        _, headers = test_user
        other = _create_user(db_session, "scorehist_other@test.com", "scorehist_other")
        other_resume = _create_resume(db_session, other.id)
        r = client.get(f"/api/resume/{other_resume.id}/score-history", headers=headers)
        assert r.status_code == 404

    def test_invalid_metric_type_rejected(self, client, test_user, db_session):
        user, headers = test_user
        resume = _create_resume(db_session, user.id)
        r = client.get(
            f"/api/resume/{resume.id}/score-history?metric_type=not_a_metric",
            headers=headers,
        )
        assert r.status_code == 422
