"""Tests for the Analytics snapshot module."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.analytics.models import ScoreSnapshot
from app.analytics.service import AnalyticsService


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
# Unit: AnalyticsService
# ---------------------------------------------------------------------------

class TestAnalyticsService:

    def test_record_snapshot_creates_record(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="career_readiness", value=75.0,
        )
        snapshots = db_session.query(ScoreSnapshot).all()
        assert len(snapshots) == 1
        assert snapshots[0].metric_type == "career_readiness"
        assert snapshots[0].value == 75.0
        assert snapshots[0].user_id == 1

    def test_dedup_skips_duplicate_value_within_interval(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0,
        )
        count = db_session.query(ScoreSnapshot).count()
        assert count == 1

    def test_different_value_creates_new_row(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=90.0,
        )
        count = db_session.query(ScoreSnapshot).count()
        assert count == 2

    def test_same_value_after_24h_creates_new_row(self, db_session):
        old = datetime(2024, 1, 1, 0, 0, 0)
        recent = datetime(2025, 6, 15, 12, 0, 0)

        snapshot = ScoreSnapshot(
            user_id=1, metric_type="career_readiness",
            value=70.0, recorded_at=old,
        )
        db_session.add(snapshot)
        db_session.commit()

        with patch("app.analytics.service.datetime") as mock_dt:
            mock_dt.utcnow.return_value = recent
            AnalyticsService.record_snapshot(
                db_session, user_id=1,
                metric_type="career_readiness", value=70.0,
            )

        count = db_session.query(ScoreSnapshot).count()
        assert count == 2

    def test_scoped_by_user(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="career_readiness", value=80.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=2, metric_type="career_readiness", value=90.0,
        )
        count_user1 = db_session.query(ScoreSnapshot).filter(
            ScoreSnapshot.user_id == 1,
        ).count()
        assert count_user1 == 1

    def test_scoped_by_metric_type(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=80.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="career_readiness", value=75.0,
        )
        count_ats = db_session.query(ScoreSnapshot).filter(
            ScoreSnapshot.metric_type == "ats_score",
        ).count()
        assert count_ats == 1

    def test_get_history_orders_by_recorded_at_asc(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="career_readiness", value=50.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="career_readiness", value=60.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="career_readiness", value=70.0,
        )
        history = AnalyticsService.get_history(
            db_session, user_id=1, metric_type="career_readiness",
        )
        values = [s.value for s in history]
        assert values == [50.0, 60.0, 70.0]

    def test_get_history_descending_returns_newest_first(self, db_session):
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=50.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=60.0,
        )
        AnalyticsService.record_snapshot(
            db_session, user_id=1, metric_type="ats_score", value=70.0,
        )
        history = AnalyticsService.get_history(
            db_session, user_id=1, metric_type="ats_score", limit=1, descending=True,
        )
        assert len(history) == 1
        assert history[0].value == 70.0

    def test_resilient_on_failure(self, db_session):
        original_add = db_session.add
        def broken_add(obj):
            raise RuntimeError("DB write failed")
        db_session.add = broken_add
        try:
            AnalyticsService.record_snapshot(
                db_session, user_id=1,
                metric_type="career_readiness", value=50.0,
            )
        finally:
            db_session.add = original_add


# ---------------------------------------------------------------------------
# API: GET /api/analytics/history
# ---------------------------------------------------------------------------

class TestAnalyticsApi:

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
        from app.models.user import User
        from app.dependencies import get_password_hash
        user = User(
            email="analytics_test@test.com",
            username="analytics_test",
            hashed_password=get_password_hash("Test1234!"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        r = client.post("/api/auth/login", json={
            "email": "analytics_test@test.com", "password": "Test1234!",
        })
        assert r.status_code == 200
        token = r.json().get("access_token", "")
        return user, {"Authorization": f"Bearer {token}"}

    def test_get_history_empty(self, client, test_user):
        _, headers = test_user
        r = client.get("/api/analytics/history?metric_type=career_readiness", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["items"] == []

    def test_get_history_returns_snapshots(self, client, test_user, db_session):
        user, headers = test_user
        AnalyticsService.record_snapshot(
            db_session, user.id, "career_readiness", 75.0,
        )
        r = client.get("/api/analytics/history?metric_type=career_readiness", headers=headers)
        assert r.status_code == 200
        items = r.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["metric_type"] == "career_readiness"
        assert items[0]["value"] == 75.0

    def test_get_history_descending_api(self, client, test_user, db_session):
        user, headers = test_user
        AnalyticsService.record_snapshot(db_session, user.id, "ats_score", 50.0)
        AnalyticsService.record_snapshot(db_session, user.id, "ats_score", 70.0)
        r = client.get(
            "/api/analytics/history?metric_type=ats_score&limit=1&descending=true",
            headers=headers,
        )
        assert r.status_code == 200
        items = r.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["value"] == 70.0

    def test_get_history_scoped_per_user(self, client, test_user, db_session):
        user_a, headers_a = test_user
        from app.models.user import User
        from app.dependencies import get_password_hash
        user_b = User(
            email="analytics_user_b@test.com", username="analytics_user_b",
            hashed_password=get_password_hash("Test1234!"), is_active=True,
        )
        db_session.add(user_b)
        db_session.commit()
        db_session.refresh(user_b)
        r = client.post("/api/auth/login", json={
            "email": "analytics_user_b@test.com", "password": "Test1234!",
        })
        headers_b = {"Authorization": f"Bearer {r.json().get('access_token', '')}"}

        AnalyticsService.record_snapshot(db_session, user_a.id, "career_readiness", 80.0)
        AnalyticsService.record_snapshot(db_session, user_b.id, "career_readiness", 90.0)

        r_a = client.get("/api/analytics/history?metric_type=career_readiness", headers=headers_a)
        r_b = client.get("/api/analytics/history?metric_type=career_readiness", headers=headers_b)
        assert r_a.status_code == 200
        assert r_b.status_code == 200
        assert len(r_a.json()["data"]["items"]) == 1
        assert r_a.json()["data"]["items"][0]["value"] == 80.0
        assert len(r_b.json()["data"]["items"]) == 1
        assert r_b.json()["data"]["items"][0]["value"] == 90.0

    def test_get_history_requires_auth(self, client):
        r = client.get("/api/analytics/history?metric_type=career_readiness")
        assert r.status_code == 401
