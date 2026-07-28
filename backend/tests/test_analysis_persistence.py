"""Phase 3K: Analysis Persistence, Caching, and Version Awareness — tests.

Tests cover:
- Create analysis record
- Retrieve analysis by ID (with auth)
- Get latest analysis for resume
- Cache hit (fresh analysis exists)
- Cache miss (no analysis exists)
- Stale detection (resume.version > analysis.resume_version)
- Version mismatch
- Re-analysis (force re-analyze endpoint)
- Concurrent request prevention (409 on duplicate)
- Authorization (User A cannot access User B's analysis)
- History listing
- Stale status endpoint
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.services.analysis_persistence_service import (
    acquire_analysis_lock,
    check_cache,
    get_analysis_by_id,
    get_analysis_history,
    get_latest_analysis,
    is_analysis_in_progress,
    mark_stale_analyses,
    release_analysis_lock,
    save_analysis,
    _extract_scores,
)

# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    user = User(
        email="persist_test@example.com",
        username="persist_test",
        hashed_password="$2b$12$abcdefghijklmnopqrstuvwx",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session):
    user = User(
        email="other@example.com",
        username="other_user",
        hashed_password="$2b$12$abcdefghijklmnopqrstuvwx",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_resume(db_session, test_user):
    resume = Resume(
        user_id=test_user.id,
        name="Test Resume",
        version=1,
        personal='{"first_name": "John", "last_name": "Doe", "email": "john@test.com"}',
        summary="Experienced software engineer with 5 years of experience.",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume


@pytest.fixture
def other_resume(db_session, other_user):
    resume = Resume(
        user_id=other_user.id,
        name="Other Resume",
        version=1,
        personal='{"first_name": "Jane", "last_name": "Smith", "email": "jane@other.com"}',
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume


@pytest.fixture
def auth_headers(test_user, db_session):
    from app.dependencies import create_access_token

    token = create_access_token({"sub": str(test_user.id), "ver": 0})

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield {"Authorization": f"Bearer {token}"}
    app.dependency_overrides.clear()


@pytest.fixture
def other_auth_headers(other_user, db_session):
    from app.dependencies import create_access_token

    token = create_access_token({"sub": str(other_user.id), "ver": 0})

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield {"Authorization": f"Bearer {token}"}
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


SAMPLE_ANALYSIS_JSON = {
    "deterministic": {
        "completeness": {"overall_completeness_score": 75},
        "overall_quality_score": {"overall_score": 72},
    },
    "quality_report": {"overall_score": 70},
    "ats_analysis": {"overall_ats_score": 65},
    "recommendations": [],
    "high_priority_recommendations": 0,
}

SAMPLE_SCORES = {"overall_score": 72, "quality_score": 70, "ats_score": 65}


# =========================================================================
# Service Tests
# =========================================================================


class TestSaveAnalysis:
    def test_create_analysis_record(self, db_session, test_user, test_resume):
        record = save_analysis(
            db=db_session,
            user_id=test_user.id,
            resume_id=test_resume.id,
            resume_version=1,
            source="deterministic",
            analysis_json=SAMPLE_ANALYSIS_JSON,
            scores_json=SAMPLE_SCORES,
        )
        assert record.id is not None
        assert record.user_id == test_user.id
        assert record.resume_id == test_resume.id
        assert record.resume_version == 1
        assert record.source == "deterministic"
        assert record.analysis_json == SAMPLE_ANALYSIS_JSON
        assert record.scores_json == SAMPLE_SCORES
        assert record.is_stale == 0
        assert record.created_at is not None

    def test_create_analysis_with_ai_source(self, db_session, test_user, test_resume):
        record = save_analysis(
            db=db_session,
            user_id=test_user.id,
            resume_id=test_resume.id,
            resume_version=2,
            source="full",
            analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        assert record.source == "full"
        assert record.scores_json is None

    def test_create_multiple_analyses(self, db_session, test_user, test_resume):
        for v in range(1, 4):
            save_analysis(
                db=db_session,
                user_id=test_user.id,
                resume_id=test_resume.id,
                resume_version=v,
                source="deterministic",
                analysis_json=SAMPLE_ANALYSIS_JSON,
            )
        history = get_analysis_history(db_session, test_resume.id, test_user.id)
        assert len(history) == 3


class TestGetLatestAnalysis:
    def test_get_latest_returns_most_recent(self, db_session, test_user, test_resume):
        save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        import time; time.sleep(0.01)
        save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=2, source="full", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        latest = get_latest_analysis(db_session, test_resume.id, test_user.id)
        assert latest is not None
        assert latest.resume_version == 2
        assert latest.source == "full"

    def test_get_latest_no_analysis(self, db_session, test_user, test_resume):
        latest = get_latest_analysis(db_session, test_resume.id, test_user.id)
        assert latest is None

    def test_get_latest_auth_prevents_other_user(self, db_session, test_user, other_user, test_resume):
        save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        latest = get_latest_analysis(db_session, test_resume.id, other_user.id)
        assert latest is None


class TestGetAnalysisById:
    def test_get_by_id_success(self, db_session, test_user, test_resume):
        record = save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        found = get_analysis_by_id(db_session, record.id, test_user.id)
        assert found is not None
        assert found.id == record.id

    def test_get_by_id_wrong_user(self, db_session, test_user, other_user, test_resume):
        record = save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        found = get_analysis_by_id(db_session, record.id, other_user.id)
        assert found is None

    def test_get_by_id_nonexistent(self, db_session, test_user):
        found = get_analysis_by_id(db_session, 9999, test_user.id)
        assert found is None


class TestCacheCheck:
    def test_cache_hit_fresh(self, db_session, test_user, test_resume):
        save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        cached, stale, record = check_cache(db_session, test_resume.id, test_user.id, resume_version=1)
        assert cached is True
        assert stale is False
        assert record is not None

    def test_cache_miss(self, db_session, test_user, test_resume):
        cached, stale, record = check_cache(db_session, test_resume.id, test_user.id, resume_version=1)
        assert cached is False
        assert stale is False
        assert record is None

    def test_cache_stale_version_mismatch(self, db_session, test_user, test_resume):
        save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        cached, stale, record = check_cache(db_session, test_resume.id, test_user.id, resume_version=2)
        assert cached is True
        assert stale is True
        assert record is not None

    def test_cache_stale_when_updated(self, db_session, test_user, test_resume):
        save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        test_resume.version = 2
        db_session.commit()
        cached, stale, record = check_cache(db_session, test_resume.id, test_user.id, resume_version=2)
        assert cached is True
        assert stale is True


class TestMarkStaleAnalyses:
    def test_mark_stale(self, db_session, test_user, test_resume):
        save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        count = mark_stale_analyses(db_session, test_resume.id, test_user.id, current_version=2)
        assert count >= 1

        latest = get_latest_analysis(db_session, test_resume.id, test_user.id)
        assert latest.is_stale == 1

    def test_mark_stale_only_older(self, db_session, test_user, test_resume):
        save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=2, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        count = mark_stale_analyses(db_session, test_resume.id, test_user.id, current_version=2)
        assert count == 0


class TestConcurrentLock:
    def test_acquire_and_release(self):
        resume_id = 42
        assert not is_analysis_in_progress(resume_id)
        assert acquire_analysis_lock(resume_id) is True
        assert is_analysis_in_progress(resume_id) is True
        assert acquire_analysis_lock(resume_id) is False
        release_analysis_lock(resume_id)
        assert not is_analysis_in_progress(resume_id)

    def test_multiple_resumes_independent(self):
        assert acquire_analysis_lock(1) is True
        assert acquire_analysis_lock(2) is True
        assert is_analysis_in_progress(1) is True
        assert is_analysis_in_progress(2) is True
        release_analysis_lock(1)
        release_analysis_lock(2)
        assert not is_analysis_in_progress(1)
        assert not is_analysis_in_progress(2)


class TestExtractScores:
    def test_extracts_all_scores(self):
        scores = _extract_scores(SAMPLE_ANALYSIS_JSON)
        assert scores["overall_score"] == 72
        assert scores["quality_score"] == 70
        assert scores["ats_score"] == 65
        assert scores["completeness_score"] == 75

    def test_extracts_from_empty(self):
        scores = _extract_scores({})
        assert scores["overall_score"] == 0


# =========================================================================
# API Tests
# =========================================================================


class TestApiGetLatest:
    def test_get_latest_no_auth(self, client, test_resume):
        response = client.get(f"/api/analysis/resume/{test_resume.id}/latest")
        assert response.status_code == 401

    def test_get_latest_nonexistent_resume(self, client, auth_headers):
        response = client.get("/api/analysis/resume/99999/latest", headers=auth_headers)
        assert response.status_code == 404

    def test_get_latest_cache_miss(self, client, auth_headers, test_resume):
        response = client.get(f"/api/analysis/resume/{test_resume.id}/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is False
        assert data["analysis"] is None

    def test_get_latest_cache_hit(self, client, auth_headers, test_resume, db_session):
        _create_analysis(db_session, test_resume, test_resume.user_id)
        response = client.get(f"/api/analysis/resume/{test_resume.id}/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["stale"] is False
        assert data["analysis"] is not None
        assert data["analysis"]["resume_version"] == 1

    def test_get_latest_cache_stale(self, client, auth_headers, test_resume, db_session):
        _create_analysis(db_session, test_resume, test_resume.user_id)
        test_resume.version = 2
        db_session.commit()
        response = client.get(f"/api/analysis/resume/{test_resume.id}/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["stale"] is True
        assert data["analysis"]["is_stale"] is True

    def test_get_latest_other_user_resume(self, client, auth_headers, other_resume):
        response = client.get(f"/api/analysis/resume/{other_resume.id}/latest", headers=auth_headers)
        assert response.status_code == 404


class TestApiGetAnalysisById:
    def test_get_by_id_success(self, client, auth_headers, test_resume, db_session):
        record = _create_analysis(db_session, test_resume, test_resume.user_id)
        response = client.get(f"/api/analysis/{record.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == record.id
        assert data["resume_id"] == test_resume.id

    def test_get_by_id_not_found(self, client, auth_headers):
        response = client.get("/api/analysis/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_by_id_other_user_analysis(self, client, auth_headers, db_session, test_resume, other_user):
        record = save_analysis(
            db=db_session, user_id=other_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        response = client.get(f"/api/analysis/{record.id}", headers=auth_headers)
        assert response.status_code == 404


class TestApiHistory:
    def test_history_empty(self, client, auth_headers, test_resume):
        response = client.get(f"/api/analysis/resume/{test_resume.id}/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["analyses"] == []
        assert data["total"] == 0

    def test_history_with_records(self, client, auth_headers, test_resume, db_session):
        _create_analysis(db_session, test_resume, test_resume.user_id)
        response = client.get(f"/api/analysis/resume/{test_resume.id}/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["current_version"] == 1

    def test_history_other_user(self, client, auth_headers, other_resume):
        response = client.get(f"/api/analysis/resume/{other_resume.id}/history", headers=auth_headers)
        assert response.status_code == 404


class TestApiStaleStatus:
    def test_stale_no_cache(self, client, auth_headers, test_resume):
        response = client.get(f"/api/analysis/resume/{test_resume.id}/stale", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["has_cached"] is False
        assert data["is_stale"] is False

    def test_stale_fresh(self, client, auth_headers, test_resume, db_session):
        _create_analysis(db_session, test_resume, test_resume.user_id)
        response = client.get(f"/api/analysis/resume/{test_resume.id}/stale", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["has_cached"] is True
        assert data["is_stale"] is False

    def test_stale_outdated(self, client, auth_headers, test_resume, db_session):
        _create_analysis(db_session, test_resume, test_resume.user_id)
        test_resume.version = 3
        db_session.commit()
        response = client.get(f"/api/analysis/resume/{test_resume.id}/stale", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["has_cached"] is True
        assert data["is_stale"] is True


class TestApiReAnalyze:
    def test_re_analyze_success(self, client, auth_headers, test_resume, db_session):
        response = client.post(
            f"/api/analysis/resume/{test_resume.id}/re-analyze",
            json={"enable_ai": False, "force": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "deterministic" in data
        assert "recommendations" in data

    def test_re_analyze_persists(self, client, auth_headers, test_resume, db_session):
        response = client.post(
            f"/api/analysis/resume/{test_resume.id}/re-analyze",
            json={"enable_ai": False, "force": True},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Check that it was persisted
        check = client.get(f"/api/analysis/resume/{test_resume.id}/latest", headers=auth_headers)
        assert check.status_code == 200
        assert check.json()["cached"] is True

    def test_re_analyze_nonexistent_resume(self, client, auth_headers):
        response = client.post(
            "/api/analysis/resume/99999/re-analyze",
            json={"enable_ai": False, "force": True},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_re_analyze_no_auth(self, client, test_resume):
        response = client.post(
            f"/api/analysis/resume/{test_resume.id}/re-analyze",
            json={"enable_ai": False, "force": True},
        )
        assert response.status_code == 401


class TestApiAnalyzeInline:
    def test_inline_analyze_without_resume_id(self, client, auth_headers):
        payload = {
            "resume": {
                "personal": {"first_name": "Test", "email": "test@test.com"},
            },
        }
        response = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_analyze_with_resume_id_persists(self, client, auth_headers, test_resume, db_session):
        payload = {
            "resume": {
                "personal": {"first_name": "John", "last_name": "Doe", "email": "john@test.com"},
                "summary": "Experienced engineer.",
            },
            "resume_id": test_resume.id,
        }
        response = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
        assert response.status_code == 200

        # Should be cached now
        check = client.get(f"/api/analysis/resume/{test_resume.id}/latest", headers=auth_headers)
        assert check.status_code == 200
        assert check.json()["cached"] is True

    def test_analyze_returns_cached_on_second_call(self, client, auth_headers, test_resume, db_session):
        payload = {
            "resume": {
                "personal": {"first_name": "John", "email": "john@test.com"},
            },
            "resume_id": test_resume.id,
        }
        first = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
        assert first.status_code == 200
        first_score = first.json()["deterministic"]["overall_quality_score"]["overall_score"]

        second = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
        assert second.status_code == 200
        second_score = second.json()["deterministic"]["overall_quality_score"]["overall_score"]

        # Same deterministic analysis → same scores
        assert first_score == second_score

    def test_analyze_wrong_user_resume(self, client, auth_headers, other_resume):
        payload = {
            "resume": {"personal": {"first_name": "Hacker", "email": "h@x.com"}},
            "resume_id": other_resume.id,
        }
        response = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_analyze_concurrent_request(self, client, auth_headers, test_resume, db_session):
        payload = {
            "resume": {"personal": {"first_name": "John", "email": "john@test.com"}},
            "resume_id": test_resume.id,
        }
        acquire_analysis_lock(test_resume.id)
        try:
            response = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
            assert response.status_code == 409
        finally:
            release_analysis_lock(test_resume.id)


class TestApiAnalyzeFromDb:
    def test_analyze_from_db_success(self, client, auth_headers, test_resume):
        response = client.post(
            f"/api/analysis/resume/{test_resume.id}/analyze",
            json={"enable_ai": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_analyze_from_db_no_auth(self, client, test_resume):
        response = client.post(
            f"/api/analysis/resume/{test_resume.id}/analyze",
            json={"enable_ai": False},
        )
        assert response.status_code == 401

    def test_analyze_from_db_nonexistent(self, client, auth_headers):
        response = client.post(
            "/api/analysis/resume/99999/analyze",
            json={"enable_ai": False},
            headers=auth_headers,
        )
        assert response.status_code == 404


# =========================================================================
# Authorization Tests
# =========================================================================


class TestAuthorization:
    def test_user_a_cannot_access_user_b_analysis(self, client, auth_headers, other_auth_headers, db_session, test_user, test_resume, other_user):
        # test_user creates analysis
        record = save_analysis(
            db=db_session, user_id=test_user.id, resume_id=test_resume.id,
            resume_version=1, source="deterministic", analysis_json=SAMPLE_ANALYSIS_JSON,
        )
        # other_user tries to access it
        response = client.get(f"/api/analysis/{record.id}", headers=other_auth_headers)
        assert response.status_code == 404

    def test_user_a_cannot_get_latest_on_user_b_resume(self, client, other_auth_headers, test_resume):
        response = client.get(f"/api/analysis/resume/{test_resume.id}/latest", headers=other_auth_headers)
        assert response.status_code == 404

    def test_user_a_cannot_re_analyze_user_b_resume(self, client, other_auth_headers, test_resume):
        response = client.post(
            f"/api/analysis/resume/{test_resume.id}/re-analyze",
            json={"enable_ai": False, "force": True},
            headers=other_auth_headers,
        )
        assert response.status_code == 404


# =========================================================================
# Helper
# =========================================================================


def _create_analysis(db_session, resume, user_id):
    return save_analysis(
        db=db_session,
        user_id=user_id,
        resume_id=resume.id,
        resume_version=resume.version,
        source="deterministic",
        analysis_json=SAMPLE_ANALYSIS_JSON,
        scores_json=SAMPLE_SCORES,
    )
