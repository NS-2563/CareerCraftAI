"""Tests for Dashboard Career Health Score — a disclosed, weighted mean of real
sub-metrics that degrades honestly ("not enough data yet") rather than guessing."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dashboard.health_score import (
    WEIGHTS,
    MIN_SUB_METRICS,
    MIN_INTERVIEW_SESSIONS,
    compute_career_health_score,
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


def _ats(db, user_id, value):
    from app.analytics.models import ScoreSnapshot
    db.add(ScoreSnapshot(user_id=user_id, metric_type="ats_score", value=value))
    db.commit()


def _interview(db, user_id, score, session_type="practice"):
    from app.interview_prep.models import InterviewSession
    db.add(InterviewSession(
        user_id=user_id, session_type=session_type, overall_score=score,
    ))
    db.commit()


def _jd(db, user_id, app_id, score):
    from app.models.jd_match_result import JDMatchResult
    db.add(JDMatchResult(
        user_id=user_id, job_application_id=app_id, match_score=score,
    ))
    db.commit()


def _login(client, email, password="Test1234!"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Unit: pure data availability gating
# ---------------------------------------------------------------------------

class TestAvailabilityGating:

    def test_no_data_at_all_is_not_enough(self, db_session):
        u = _create_user(db_session, "empty@health.com", "empty_health")
        result = compute_career_health_score(db_session, u.id)
        assert result["available"] is False
        assert result["score"] is None
        assert result["reason"] == "not enough data yet"
        assert result["minimum_sub_metric_reason"]

    def test_single_sub_metric_is_not_enough(self, db_session):
        u = _create_user(db_session, "one@health.com", "one")
        _ats(db_session, u.id, 80)
        score = compute_career_health_score(db_session, u.id)
        assert score["available"] is False
        assert score["score"] is None
        assert score["reason"] == "not enough data yet"

    def test_all_sub_metrics_report_availability_flags(self, db_session):
        u = _create_user(db_session, "flags@health.com", "flags")
        _ats(db_session, u.id, 80)
        result = compute_career_health_score(db_session, u.id)
        by_key = {m["key"]: m for m in result["sub_metrics"]}
        assert by_key["ats"]["available"] is True
        assert by_key["interview"]["available"] is False
        assert by_key["jd_match"]["available"] is False


# ---------------------------------------------------------------------------
# Unit: weighted formula
# ---------------------------------------------------------------------------

class TestWeightedFormula:

    def test_two_metrics_redistribute_weights(self, db_session):
        u = _create_user(db_session, "two@health.com", "two")
        _ats(db_session, u.id, 80)
        for _ in range(MIN_INTERVIEW_SESSIONS):
            _interview(db_session, u.id, 90)

        result = compute_career_health_score(db_session, u.id)
        assert result["available"] is True
        by_key = {m["key"]: m for m in result["sub_metrics"]}
        # available: ats (0.40) + interview (0.30) -> effective weights sum to 1
        effective_ats = by_key["ats"]["effective_weight"]
        effective_int = by_key["interview"]["effective_weight"]
        assert abs(effective_ats - 0.4 / 0.7) < 0.001
        assert abs(effective_int - 0.3 / 0.7) < 0.001
        assert abs(effective_ats + effective_int - 1.0) < 0.001
        # 80*0.5714 + 90*0.4286 = 84.3
        assert result["score"] == 84.3

    def test_all_three_metrics_use_documented_weights(self, db_session):
        u = _create_user(db_session, "all@home.com", "all")
        _ats(db_session, u.id, 80)
        for _ in range(MIN_INTERVIEW_SESSIONS):
            _interview(db_session, u.id, 70)
        _jd(db_session, u.id, app_id=1, score=60)

        result = compute_career_health_score(db_session, u.id)
        assert result["score"] == round(80*0.4 + 70*0.3 + 60*0.3, 1)  # 71.0
        for m in result["sub_metrics"]:
            assert m["effective_weight"] == m["weight"]  # all available


# ---------------------------------------------------------------------------
# Per-sub-metric source correctness
# ---------------------------------------------------------------------------

class TestSubMetrics:

    def test_ats_uses_latest_snapshot(self, db_session):
        u = _create_user(db_session, "lat@home.com", "lat")
        _ats(db_session, u.id, 40)
        _ats(db_session, u.id, 90)
        for _ in range(MIN_INTERVIEW_SESSIONS):
            _interview(db_session, u.id, 70)
        _jd(db_session, u.id, app_id=1, score=70)
        result = compute_career_health_score(db_session, u.id)
        assert result["available"] is True
        assert result["score"] == round(90*0.4 + 70*0.3 + 70*0.3, 1)  # 78.0

    def test_ats_clamped_to_100(self, db_session):
        u = _create_user(db_session, "clamp@home.com", "clamp")
        _ats(db_session, u.id, 150)
        for _ in range(MIN_INTERVIEW_SESSIONS):
            _interview(db_session, u.id, 70)
        _jd(db_session, u.id, app_id=1, score=70)
        result = compute_career_health_score(db_session, u.id)
        assert result["available"] is True
        assert result["score"] == round(100*0.4 + 70*0.3 + 70*0.3, 1)  # 82.0

    def test_interview_requires_min_sessions(self, db_session):
        u = _create_user(db_session, "fewint@home.com", "fewint")
        _ats(db_session, u.id, 80)
        # only 2 practice sessions -> under the threshold of 3
        _interview(db_session, u.id, 70)
        _interview(db_session, u.id, 70)
        result = compute_career_health_score(db_session, u.id)
        by_key = {m["key"]: m for m in result["sub_metrics"]}
        assert by_key["interview"]["available"] is False
        # only ats available -> not enough data
        assert result["available"] is False

    def test_real_interview_sessions_not_counted(self, db_session):
        u = _create_user(db_session, "realint@home.com", "realint")
        _ats(db_session, u.id, 80)
        # 3 REAL interviews with scores -> must NOT satisfy the practice min
        for _ in range(3):
            _interview(db_session, u.id, 90, session_type="real_interview")
        result = compute_career_health_score(db_session, u.id)
        by_key = {m["key"]: m for m in result["sub_metrics"]}
        assert by_key["interview"]["available"] is False
        assert result["available"] is False

    def test_jd_averages_latest_result_per_application(self, db_session):
        u = _create_user(db_session, "jdavg@home.com", "jdavg")
        _ats(db_session, u.id, 80)
        for _ in range(MIN_INTERVIEW_SESSIONS):
            _interview(db_session, u.id, 80)
        # app 1: old 40, new 100 -> only 100 counts
        _jd(db_session, u.id, app_id=1, score=40)
        _jd(db_session, u.id, app_id=1, score=100)
        # app 2: 50
        _jd(db_session, u.id, app_id=2, score=50)
        result = compute_career_health_score(db_session, u.id)
        by_key = {m["key"]: m for m in result["sub_metrics"]}
        # jd average = (100 + 50) / 2 = 75
        assert by_key["jd_match"]["value"] == 75.0
        assert result["score"] == round(80*0.4 + 80*0.3 + 75*0.3, 1)  # 78.5


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class TestHealthScoreApi:

    def test_requires_auth(self, client):
        resp = client.get("/api/dashboard/health-score")
        assert resp.status_code == 401

    def test_new_user_not_enough_data(self, db_session, client):
        _create_user(db_session, "newapi@home.com", "newapi")
        token = _login(client, "newapi@home.com")
        resp = client.get(
            "/api/dashboard/health-score",
            headers=_headers(token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["available"] is False
        assert data["score"] is None
        assert data["reason"] == "not enough data yet"
        assert len(data["sub_metrics"]) == 3

    def test_full_user_returns_score_with_explanation(self, db_session, client):
        u = _create_user(db_session, "fullapi@home.com", "fullapi")
        _ats(db_session, u.id, 80)
        for _ in range(MIN_INTERVIEW_SESSIONS):
            _interview(db_session, u.id, 70)
        _jd(db_session, u.id, app_id=1, score=60)
        token = _login(client, "fullapi@home.com")
        resp = client.get(
            "/api/dashboard/health-score",
            headers=_headers(token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["available"] is True
        assert data["score"] == 71.0
        by_key = {m["key"]: m for m in data["sub_metrics"]}
        assert by_key["ats"]["value"] == 80.0
        assert by_key["interview"]["value"] == 70.0
        assert by_key["jd_match"]["value"] == 60.0
        assert by_key["jd_match"]["effective_weight"] == by_key["jd_match"]["weight"]

    def test_scoped_per_user(self, db_session, client):
        u_a = _create_user(db_session, "scopea@home.com", "scopea")
        _ats(db_session, u_a.id, 80)
        for _ in range(MIN_INTERVIEW_SESSIONS):
            _interview(db_session, u_a.id, 80)
        _jd(db_session, u_a.id, app_id=1, score=80)
        _create_user(db_session, "scopeb@home.com", "scopeb")
        token = _login(client, "scopeb@home.com")
        resp = client.get(
            "/api/dashboard/health-score",
            headers=_headers(token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["available"] is False