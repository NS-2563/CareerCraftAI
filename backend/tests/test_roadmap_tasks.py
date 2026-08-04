"""Tests for Career Coach roadmap task statuses, confidence buckets, and readiness history.

Covers:
- confidence bucket is a pure derivation of known supported/total signal counts
- task statuses persist across a roadmap refresh (matched by skill identity)
- readiness snapshots accumulate over time
- task-status endpoints are ownership-checked and validate their input
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Import EVERY model so create_all resolves all foreign keys/relationships.
from app.models.user import User  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.career_report import CareerReport  # noqa: F401
from app.models.job_application import JobApplication  # noqa: F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: F401
from app.models.cover_letter import CoverLetter  # noqa: F401
from app.models.jd_match_result import JDMatchResult  # noqa: F401
from app.models.roadmap_task_status import RoadmapTaskStatus  # noqa: F401
from app.communication.models import CommunicationMessage, CommunicationSuggestion  # noqa: F401
from app.interview_prep.models import InterviewSession  # noqa: F401
from app.analytics.models import ScoreSnapshot  # noqa: F401


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

def _create_user(db, email="tasks@test.com", username="taskstester",
                 password="Test1234!"):
    from app.dependencies import get_password_hash
    u = User(email=email, username=username,
             hashed_password=get_password_hash(password), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _report(priority=("Docker",), roadmap_topics=("Python",), missing_skills=()):
    return {
        "career_goal": "Backend Engineer",
        "readiness_score": 70,
        "readiness_status": "Good",
        "best_match": "Backend Engineer",
        "career_summary": "Solid.",
        "strengths": ["Python"],
        "weaknesses": ["Docker"],
        "skill_gap": {
            "existing_skills": ["Python"],
            "missing_skills": list(missing_skills),
            "priority": list(priority),
        },
        "roadmap": [{"stage": "Foundation", "topics": list(roadmap_topics), "projects": []}],
        "action_plan": {"next_week": [], "next_month": [], "next_6_months": []},
        "resources": [],
    }


def _seed_report(db, user_id, report):
    from app.career.services.history_service import save_report
    return save_report(db=db, user_id=user_id, report=report, source="ai")


# ---------------------------------------------------------------------------
# Confidence bucket (pure derivation of real signal counts)
# ---------------------------------------------------------------------------

class TestConfidenceBucket:

    def test_high_at_or_above_three_quarters(self, db_session):
        from app.career.services.recommendation_signals import confidence_label
        assert confidence_label(3, 4) == "high"    # 0.75
        assert confidence_label(4, 4) == "high"    # 1.00
        assert confidence_label(6, 8) == "high"    # 0.75

    def test_medium_between_two_fifths_and_below_three_quarters(self, db_session):
        from app.career.services.recommendation_signals import confidence_label
        assert confidence_label(2, 5) == "medium"  # 0.40
        assert confidence_label(1, 2) == "medium"  # 0.50
        assert confidence_label(2, 3) == "medium"  # 0.67

    def test_low_below_two_fifths(self, db_session):
        from app.career.services.recommendation_signals import confidence_label
        assert confidence_label(1, 3) == "low"     # 0.33
        assert confidence_label(1, 4) == "low"     # 0.25

    def test_zero_supported_is_low(self, db_session):
        from app.career.services.recommendation_signals import confidence_label
        assert confidence_label(0, 4) == "low"
        assert confidence_label(0, 1) == "low"

    def test_no_evaluable_signals_is_low(self, db_session):
        from app.career.services.recommendation_signals import confidence_label
        assert confidence_label(0, 0) == "low"

    def test_enriched_entry_carries_confidence(self, db_session):
        user = _create_user(db_session)
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        report = _report(priority=["Docker"], roadmap_topics=["Python", "Docker"])
        entries = enrich_priority_recommendations(report, db_session, user.id)
        entry = entries[0]
        # Roadmap reinforcement is the only evaluable signal -> 1/1 = high.
        assert entry["supported_signals"] == 1
        assert entry["total_possible_signals"] == 1
        assert entry["confidence"] == "high"


# ---------------------------------------------------------------------------
# Task status persistence (independent of regeneration)
# ---------------------------------------------------------------------------

class TestTaskStatusPersistence:

    def test_attach_creates_not_started_rows(self, db_session):
        user = _create_user(db_session)
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import attach_task_statuses

        report = _report(priority=["Docker"], roadmap_topics=["Python"])
        report["skill_gap"]["priority"] = enrich_priority_recommendations(report, db_session, user.id)
        attach_task_statuses(db_session, user.id, report)

        entry = report["skill_gap"]["priority"][0]
        assert entry["task_id"] is not None
        assert entry["task_status"] == "not_started"
        assert entry["task_status_settable"] is True

        from app.models.roadmap_task_status import RoadmapTaskStatus
        rows = db_session.query(RoadmapTaskStatus).filter_by(user_id=user.id).all()
        assert len(rows) == 1
        assert rows[0].skill_key == "docker"

    def test_status_survives_refresh_with_same_skill(self, db_session):
        user = _create_user(db_session)
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import (
            attach_task_statuses,
            set_task_status,
        )

        first = _report(priority=["Docker"], roadmap_topics=["Python"])
        first["skill_gap"]["priority"] = enrich_priority_recommendations(first, db_session, user.id)
        attach_task_statuses(db_session, user.id, first)
        task_id = first["skill_gap"]["priority"][0]["task_id"]

        set_task_status(db_session, task_id, user.id, "done")

        # "Refresh": a freshly regenerated report recommends the same skill.
        second = _report(priority=["Docker"], roadmap_topics=["Python"])
        second["skill_gap"]["priority"] = enrich_priority_recommendations(second, db_session, user.id)
        attach_task_statuses(db_session, user.id, second)

        entry = second["skill_gap"]["priority"][0]
        assert entry["task_id"] == task_id
        assert entry["task_status"] == "done"

    def test_status_matches_by_skill_not_position(self, db_session):
        user = _create_user(db_session)
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import (
            attach_task_statuses,
            set_task_status,
        )

        first = _report(priority=["Docker", "Kubernetes"], roadmap_topics=["Python", "Docker"])
        first["skill_gap"]["priority"] = enrich_priority_recommendations(first, db_session, user.id)
        attach_task_statuses(db_session, user.id, first)
        rows = {e["skill"]: e for e in first["skill_gap"]["priority"]}
        set_task_status(db_session, rows["Docker"]["task_id"], user.id, "in_progress")
        set_task_status(db_session, rows["Kubernetes"]["task_id"], user.id, "done")

        # Refresh reorders: Kubernetes first, Docker second.
        second = _report(priority=["Kubernetes", "Docker"], roadmap_topics=["Python", "Docker"])
        second["skill_gap"]["priority"] = enrich_priority_recommendations(second, db_session, user.id)
        attach_task_statuses(db_session, user.id, second)
        entries = {e["skill"]: e for e in second["skill_gap"]["priority"]}

        assert entries["Docker"]["task_status"] == "in_progress"
        assert entries["Kubernetes"]["task_status"] == "done"

    def test_new_skill_defaults_to_not_started_after_refresh(self, db_session):
        user = _create_user(db_session)
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import (
            attach_task_statuses,
            set_task_status,
        )

        first = _report(priority=["Docker"], roadmap_topics=["Python"])
        first["skill_gap"]["priority"] = enrich_priority_recommendations(first, db_session, user.id)
        attach_task_statuses(db_session, user.id, first)
        set_task_status(db_session, first["skill_gap"]["priority"][0]["task_id"], user.id, "done")

        second = _report(priority=["Docker", "Kubernetes"], roadmap_topics=["Python", "Docker"])
        second["skill_gap"]["priority"] = enrich_priority_recommendations(second, db_session, user.id)
        attach_task_statuses(db_session, user.id, second)
        entries = {e["skill"]: e for e in second["skill_gap"]["priority"]}

        assert entries["Docker"]["task_status"] == "done"
        assert entries["Kubernetes"]["task_status"] == "not_started"

    def test_plain_string_entries_untouched(self, db_session):
        user = _create_user(db_session)
        from app.career.services.roadmap_task_service import attach_task_statuses

        report = _report(priority=["Docker"], roadmap_topics=["Python"])
        attach_task_statuses(db_session, user.id, report)
        # No dict entries -> nothing to attach to; the list is unchanged.
        assert report["skill_gap"]["priority"] == ["Docker"]

    def test_confidence_backfilled_for_old_reports(self, db_session):
        user = _create_user(db_session)
        from app.career.services.roadmap_task_service import attach_task_statuses

        report = _report(priority=[], roadmap_topics=["Python"])
        report["skill_gap"]["priority"] = [
            {"skill": "Docker", "supported_signals": 3, "total_possible_signals": 4},
        ]
        attach_task_statuses(db_session, user.id, report)
        entry = report["skill_gap"]["priority"][0]
        assert entry["confidence"] == "high"

    def test_set_task_status_requires_ownership(self, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        other = _create_user(db_session, email="other@test.com", username="other")
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import (
            attach_task_statuses,
            get_task_status,
            set_task_status,
        )

        report = _report(priority=["Docker"], roadmap_topics=["Python"])
        report["skill_gap"]["priority"] = enrich_priority_recommendations(report, db_session, owner.id)
        attach_task_statuses(db_session, owner.id, report)
        task_id = report["skill_gap"]["priority"][0]["task_id"]

        assert get_task_status(db_session, task_id, other.id) is None
        assert set_task_status(db_session, task_id, other.id, "done") is None
        # Owner's row is unchanged.
        assert get_task_status(db_session, task_id, owner.id).status == "not_started"

    def test_set_task_status_rejects_invalid_value(self, db_session):
        user = _create_user(db_session)
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import (
            attach_task_statuses,
            set_task_status,
        )
        report = _report(priority=["Docker"], roadmap_topics=["Python"])
        report["skill_gap"]["priority"] = enrich_priority_recommendations(report, db_session, user.id)
        attach_task_statuses(db_session, user.id, report)
        task_id = report["skill_gap"]["priority"][0]["task_id"]

        with pytest.raises(ValueError):
            set_task_status(db_session, task_id, user.id, "maybe")


# ---------------------------------------------------------------------------
# generated_at timestamp
# ---------------------------------------------------------------------------

class TestGeneratedAt:

    def test_ai_branch_embeds_generated_at(self, db_session, monkeypatch):
        user = _create_user(db_session)

        def fake_generate_json(prompt=None, schema=None):
            return {"success": True, "data": _report(
                priority=["Docker"], roadmap_topics=["Python", "Docker"],
                missing_skills=["Docker"],
            )}

        monkeypatch.setattr(
            "app.career.services.roadmap_service.generate_json",
            fake_generate_json,
        )

        from app.career.services.roadmap_service import generate_career_report
        result = generate_career_report(
            {"goal": "Backend Engineer", "skills": "Python"},
            db=db_session,
            user_id=user.id,
        )
        assert result.get("success") is True
        assert result["data"].get("generated_at")

    def test_fallback_branch_embeds_generated_at(self, db_session, monkeypatch):
        user = _create_user(db_session)

        def failing_generate_json(prompt=None, schema=None):
            return {"success": False}

        monkeypatch.setattr(
            "app.career.services.roadmap_service.generate_json",
            failing_generate_json,
        )

        from app.career.services.roadmap_service import generate_career_report
        result = generate_career_report({}, db=db_session, user_id=user.id)
        assert result.get("source") == "fallback"
        assert result["data"].get("generated_at")


# ---------------------------------------------------------------------------
# Readiness snapshots accumulate
# ---------------------------------------------------------------------------

class TestReadinessSnapshots:

    def test_snapshots_accumulate_over_time(self, db_session):
        from app.analytics.service import AnalyticsService
        from app.analytics.models import ScoreSnapshot

        AnalyticsService.record_snapshot(db_session, 1, "career_readiness", 60.0)
        AnalyticsService.record_snapshot(db_session, 1, "career_readiness", 70.0)
        AnalyticsService.record_snapshot(db_session, 1, "career_readiness", 80.0)

        rows = (
            db_session.query(ScoreSnapshot)
            .filter_by(user_id=1, metric_type="career_readiness")
            .order_by(ScoreSnapshot.recorded_at.asc())
            .all()
        )
        assert [r.value for r in rows] == [60.0, 70.0, 80.0]

    def test_same_value_within_interval_dedups(self, db_session):
        from app.analytics.service import AnalyticsService
        from app.analytics.models import ScoreSnapshot

        AnalyticsService.record_snapshot(db_session, 1, "career_readiness", 75.0)
        AnalyticsService.record_snapshot(db_session, 1, "career_readiness", 75.0)
        count = (
            db_session.query(ScoreSnapshot)
            .filter_by(user_id=1, metric_type="career_readiness")
            .count()
        )
        assert count == 1

    def test_get_history_is_oldest_first(self, db_session):
        from app.analytics.service import AnalyticsService

        AnalyticsService.record_snapshot(db_session, 1, "career_readiness", 50.0)
        AnalyticsService.record_snapshot(db_session, 1, "career_readiness", 90.0)
        rows = AnalyticsService.get_history(db_session, 1, "career_readiness")
        assert [r.value for r in rows] == [50.0, 90.0]


# ---------------------------------------------------------------------------
# Task status + refresh API
# ---------------------------------------------------------------------------

class TestRoadmapApi:

    @pytest.fixture
    def client(self, db_session):
        def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def auth_headers(self, db_session, client):
        from app.dependencies import get_password_hash
        user = User(
            email="api_owner@test.com",
            username="api_owner",
            hashed_password=get_password_hash("Test1234!"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        r = client.post("/api/auth/login", json={
            "email": "api_owner@test.com", "password": "Test1234!",
        })
        assert r.status_code == 200
        token = r.json().get("access_token", "")
        return user, {"Authorization": f"Bearer {token}"}

    def _seed_task(self, db, user_id, skill="Docker"):
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import attach_task_statuses
        report = _report(priority=[skill], roadmap_topics=["Python"])
        report["skill_gap"]["priority"] = enrich_priority_recommendations(report, db, user_id)
        attach_task_statuses(db, user_id, report)
        return report["skill_gap"]["priority"][0]["task_id"]

    def test_get_status_requires_auth(self, client):
        r = client.get("/api/career/roadmap/tasks/1/status")
        assert r.status_code == 401

    def test_get_status_returns_task(self, client, db_session, auth_headers):
        user, headers = auth_headers
        task_id = self._seed_task(db_session, user.id)
        r = client.get(f"/api/career/roadmap/tasks/{task_id}/status", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["task_id"] == task_id
        assert body["skill"] == "Docker"
        assert body["status"] == "not_started"

    def test_get_status_404_for_other_user(self, client, db_session, auth_headers):
        user, headers = auth_headers
        from app.dependencies import get_password_hash
        other = User(
            email="api_other@test.com", username="api_other",
            hashed_password=get_password_hash("Test1234!"), is_active=True,
        )
        db_session.add(other)
        db_session.commit()
        db_session.refresh(other)
        r = client.post("/api/auth/login", json={
            "email": "api_other@test.com", "password": "Test1234!",
        })
        headers_other = {"Authorization": f"Bearer {r.json().get('access_token', '')}"}

        task_id = self._seed_task(db_session, user.id)
        assert client.get(
            f"/api/career/roadmap/tasks/{task_id}/status", headers=headers_other
        ).status_code == 404

    def test_put_status_updates_and_persists(self, client, db_session, auth_headers):
        user, headers = auth_headers
        task_id = self._seed_task(db_session, user.id)
        r = client.put(f"/api/career/roadmap/tasks/{task_id}/status",
                       json={"status": "in_progress"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

        get = client.get(f"/api/career/roadmap/tasks/{task_id}/status", headers=headers)
        assert get.json()["status"] == "in_progress"

    def test_put_status_rejects_invalid_value(self, client, db_session, auth_headers):
        user, headers = auth_headers
        task_id = self._seed_task(db_session, user.id)
        r = client.put(f"/api/career/roadmap/tasks/{task_id}/status",
                       json={"status": "maybe"}, headers=headers)
        assert r.status_code == 422

    def test_put_status_ownership_enforced(self, client, db_session, auth_headers):
        user, headers = auth_headers
        from app.dependencies import get_password_hash
        other = User(
            email="api_put_other@test.com", username="api_put_other",
            hashed_password=get_password_hash("Test1234!"), is_active=True,
        )
        db_session.add(other)
        db_session.commit()
        db_session.refresh(other)
        r = client.post("/api/auth/login", json={
            "email": "api_put_other@test.com", "password": "Test1234!",
        })
        headers_other = {"Authorization": f"Bearer {r.json().get('access_token', '')}"}

        task_id = self._seed_task(db_session, user.id)
        r = client.put(f"/api/career/roadmap/tasks/{task_id}/status",
                       json={"status": "done"}, headers=headers_other)
        assert r.status_code == 404

    def test_refresh_regenerates_and_keeps_task_status(self, client, db_session, auth_headers, monkeypatch):
        user, headers = auth_headers
        _seed_report(db_session, user.id, _report())

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import (
            attach_task_statuses,
            set_task_status,
        )
        first = _report(priority=["Docker"], roadmap_topics=["Python", "Docker"])
        first["skill_gap"]["priority"] = enrich_priority_recommendations(first, db_session, user.id)
        attach_task_statuses(db_session, user.id, first)
        set_task_status(db_session, first["skill_gap"]["priority"][0]["task_id"], user.id, "done")

        def fake_generate_career_report(data, db, user_id):
            data = _report(
                priority=["Docker"], roadmap_topics=["Python", "Docker"],
                missing_skills=["Docker"],
            )
            data["generated_at"] = "2026-08-02T12:00:00+00:00"
            data["skill_gap"]["priority"] = [{
                "skill": "Docker",
                "supported_signals": 2,
                "total_possible_signals": 2,
                "reasons": [
                    "Missing in 3 of 3 saved job matches",
                    "Reinforced in your learning roadmap",
                ],
                "confidence": "high",
            }]
            return {"success": True, "data": data, "source": "ai"}

        monkeypatch.setattr(
            "app.career.roadmap_router.generate_career_report",
            fake_generate_career_report,
        )

        r = client.post("/api/career/roadmap/refresh", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body.get("generated_at")
        entry = body["skill_gap"]["priority"][0]
        assert entry["skill"] == "Docker"
        assert entry["task_status"] == "done"
        assert entry["confidence"] == "high"

        # A new history row was created and a readiness snapshot recorded.
        assert len(_history(db_session, user.id)) == 2
        from app.analytics.models import ScoreSnapshot
        snapshots = (
            db_session.query(ScoreSnapshot)
            .filter_by(user_id=user.id, metric_type="career_readiness")
            .all()
        )
        assert len(snapshots) == 1

    def test_refresh_404_without_existing_report(self, client, auth_headers):
        _, headers = auth_headers
        r = client.post("/api/career/roadmap/refresh", headers=headers)
        assert r.status_code == 404

    def test_history_includes_task_statuses(self, client, db_session, auth_headers):
        user, headers = auth_headers
        seed = _report(priority=[], roadmap_topics=["Python", "Docker"])
        seed["skill_gap"]["priority"] = [{"skill": "Docker"}]
        _seed_report(db_session, user.id, seed)
        from app.career.services.recommendation_signals import enrich_priority_recommendations
        from app.career.services.roadmap_task_service import (
            attach_task_statuses,
            set_task_status,
        )
        report = _report(priority=["Docker"], roadmap_topics=["Python", "Docker"])
        report["skill_gap"]["priority"] = enrich_priority_recommendations(report, db_session, user.id)
        attach_task_statuses(db_session, user.id, report)
        set_task_status(db_session, report["skill_gap"]["priority"][0]["task_id"], user.id, "done")

        r = client.get("/career/history", headers=headers)
        assert r.status_code == 200
        item = r.json()[0]
        entry = item["report_json"]["skill_gap"]["priority"][0]
        assert entry["task_id"] is not None
        assert entry["task_status"] == "done"


def _history(db, user_id):
    from app.models.career_report import CareerReport
    return (
        db.query(CareerReport)
        .filter(CareerReport.user_id == user_id)
        .all()
    )
