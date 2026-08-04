"""Tests for Cover Letter Studio transparency features.

Covers:
- deterministic ATS keyword coverage reusing the JD matcher's extractor
- the missing-info pre-flight validation (pure + API)
- the deterministic version diff endpoint against known letter versions
- generation metadata being persisted/returned on the save path
"""

import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.services.cover_letter_ats import compute_keyword_coverage
from app.services.cover_letter_diff import compute_cover_letter_diff
from app.services.cover_letter_service import check_generation_prerequisites
from app.analysis.deterministic.jd_matcher import _extract_keywords


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


def _create_user(db, email="cl@test.com", username="cl_user"):
    from app.models.user import User
    from app.dependencies import get_password_hash
    u = User(email=email, username=username,
             hashed_password=get_password_hash("Test1234!"), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_cover_letter(db, user_id, content="Dear Hiring Manager,\nI apply.\nAlice",
                         job_description="Python Docker Kubernetes", version=1):
    from app.models.cover_letter import CoverLetter
    cl = CoverLetter(
        user_id=user_id,
        title="Engineer Letter",
        content=content,
        job_title="Software Engineer",
        company_name="Acme",
        job_description=job_description,
        tone="professional",
        template="modern",
        version=version,
        version_history="[]",
    )
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl


# ---------------------------------------------------------------------------
# ATS keyword coverage (pure, reuses JD matcher extraction)
# ---------------------------------------------------------------------------

class TestKeywordCoverage:

    def test_reuses_jd_matcher_extraction(self):
        """The letter keyword set must come from the same extractor the JD matcher uses."""
        jd = "Python Docker Kubernetes"
        letter = "I am proficient in Python and Docker."
        result = compute_keyword_coverage(jd, letter)
        jd_keywords = set(_extract_keywords(jd))
        letter_keywords = set(_extract_keywords(letter))
        assert set(result["covered_keywords"]) == jd_keywords & letter_keywords
        assert result["total_keywords"] == len(jd_keywords)

    def test_known_pair_partial_coverage(self):
        result = compute_keyword_coverage(
            "Python Docker Kubernetes",
            "I am proficient in Python and Docker.",
        )
        assert result["covered_keywords"] == ["docker", "python"]
        assert result["missing_keywords"] == ["kubernetes"]
        assert result["covered_count"] == 2
        assert result["total_keywords"] == 3
        assert result["label"] == "2 of 3 keywords present"

    def test_known_pair_full_coverage(self):
        result = compute_keyword_coverage(
            "Python Docker Kubernetes",
            "Python, Docker and Kubernetes experience.",
        )
        assert result["covered_count"] == 3
        assert result["missing_keywords"] == []
        assert result["label"] == "3 of 3 keywords present"

    def test_known_pair_zero_coverage(self):
        result = compute_keyword_coverage(
            "Python Docker Kubernetes",
            "I enjoy gardening and cooking.",
        )
        assert result["covered_count"] == 0
        assert result["missing_keywords"] == ["docker", "kubernetes", "python"]
        assert result["label"] == "0 of 3 keywords present"

    def test_no_job_description(self):
        result = compute_keyword_coverage(None, "Some letter text.")
        assert result["covered_count"] == 0
        assert result["total_keywords"] == 0
        assert result["covered_keywords"] == []
        assert result["missing_keywords"] == []
        assert result["label"] == "No job description to check"

    def test_empty_inputs(self):
        result = compute_keyword_coverage("", "")
        assert result["total_keywords"] == 0
        assert result["covered_keywords"] == []

    def test_case_insensitive(self):
        result = compute_keyword_coverage("PYTHON", "python")
        assert result["covered_count"] == 1
        assert result["covered_keywords"] == ["python"]

    def test_stop_words_and_short_tokens_excluded(self):
        jd = "Cloud infrastructure with Python required"
        result = compute_keyword_coverage(jd, "python")
        jd_keywords = _extract_keywords(jd)
        assert "cloud" in jd_keywords  # significant token kept
        assert "infrastructure" in jd_keywords  # significant token kept
        assert "with" not in jd_keywords  # stop word dropped
        assert "required" not in jd_keywords  # stop word dropped
        assert result["covered_keywords"] == ["python"]


# ---------------------------------------------------------------------------
# Missing-info pre-flight validation (pure)
# ---------------------------------------------------------------------------

class TestPreflightValidation:

    def test_all_missing(self):
        missing = check_generation_prerequisites(None, "", "", None)
        assert missing == ["resume", "job title", "company name", "job description"]

    def test_only_company_missing(self):
        missing = check_generation_prerequisites(1, "Engineer", "", "JD text")
        assert missing == ["company name"]

    def test_only_job_description_missing(self):
        missing = check_generation_prerequisites(1, "Engineer", "Acme", "   ")
        assert missing == ["job description"]

    def test_whitespace_only_company_is_missing(self):
        missing = check_generation_prerequisites(1, "Engineer", "   ", "JD")
        assert missing == ["company name"]

    def test_ready_when_all_present(self):
        missing = check_generation_prerequisites(1, "Engineer", "Acme", "JD text")
        assert missing == []


# ---------------------------------------------------------------------------
# Diff computation (pure)
# ---------------------------------------------------------------------------

class TestDiffComputation:

    def test_known_versions(self):
        v1 = "Dear Hiring Manager,\nI am applying for the role.\nSincerely,\nAlice"
        v2 = "Dear Hiring Manager,\nI am applying for the role at Acme.\nSincerely,\nAlice"
        diff = compute_cover_letter_diff(v1, v2)
        assert diff["from_line_count"] == 4
        assert diff["to_line_count"] == 4
        assert diff["lines_added"] == 1
        assert diff["lines_removed"] == 1
        assert diff["word_count_delta"] == 2  # "at Acme" added = two words
        assert len(diff["changes"]) == 1
        change = diff["changes"][0]
        assert change["type"] == "replace"
        assert change["removed"] == ["I am applying for the role."]
        assert change["added"] == ["I am applying for the role at Acme."]

    def test_identical_texts(self):
        diff = compute_cover_letter_diff("Same text\nhere", "Same text\nhere")
        assert diff["lines_added"] == 0
        assert diff["lines_removed"] == 0
        assert diff["word_count_delta"] == 0
        assert diff["changes"] == []

    def test_word_count_delta_negative(self):
        v1 = "one two three four five"
        v2 = "one"
        diff = compute_cover_letter_diff(v1, v2)
        assert diff["word_count_delta"] == -4

    def test_none_texts_treated_as_empty(self):
        diff = compute_cover_letter_diff(None, None)
        assert diff["from_line_count"] == 0
        assert diff["to_line_count"] == 0
        assert diff["changes"] == []


# ---------------------------------------------------------------------------
# API: preflight + diff + metadata
# ---------------------------------------------------------------------------

class TestCoverLetterTransparencyApi:

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
        # Mint the token directly (repo pattern) to avoid the global login
        # rate limit (10/min per TestClient) that flakes API test suites.
        from app.dependencies import create_access_token
        user = _create_user(db_session)
        token = create_access_token(data={"sub": str(user.id)})
        return user, {"Authorization": f"Bearer {token}"}

    # -- Preflight API ------------------------------------------------------

    def test_preflight_reports_all_missing(self, client, test_user):
        _, headers = test_user
        r = client.post("/api/cover-letter/preflight", json={}, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["ready"] is False
        assert data["missing"] == ["resume", "job title", "company name", "job description"]

    def test_preflight_reports_partial_missing(self, client, test_user):
        _, headers = test_user
        r = client.post("/api/cover-letter/preflight", json={
            "resume_id": 1, "company_name": "Acme", "job_description": "JD",
        }, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["ready"] is False
        assert data["missing"] == ["job title"]

    def test_preflight_ready(self, client, test_user):
        _, headers = test_user
        r = client.post("/api/cover-letter/preflight", json={
            "resume_id": 1, "job_title": "Engineer", "company_name": "Acme",
            "job_description": "JD text",
        }, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["ready"] is True
        assert data["missing"] == []

    def test_preflight_requires_auth(self, client):
        r = client.post("/api/cover-letter/preflight", json={})
        assert r.status_code == 401

    # -- ATS coverage endpoint ----------------------------------------------

    def test_ats_coverage_endpoint(self, client, test_user, db_session):
        user, headers = test_user
        cl = _create_cover_letter(db_session, user.id, content="Python and Docker experience.")
        r = client.get(f"/api/cover-letter/{cl.id}/ats-coverage", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total_keywords"] == 3
        assert data["covered_count"] == 2
        assert data["label"] == "2 of 3 keywords present"

    def test_ats_coverage_ownership(self, client, test_user, db_session):
        user, headers = test_user
        other = _create_user(db_session, email="other@test.com", username="other_user")
        cl = _create_cover_letter(db_session, other.id)
        r = client.get(f"/api/cover-letter/{cl.id}/ats-coverage", headers=headers)
        assert r.status_code == 404

    # -- Diff endpoint ------------------------------------------------------

    def _seed_versions(self, db, user):
        cl = _create_cover_letter(
            db, user.id,
            content="Dear Hiring Manager,\nI am applying for the role.\nSincerely,\nAlice",
        )
        from app.services.cover_letter_service import CoverLetterService
        from app.schemas.cover_letter import CoverLetterUpdate
        CoverLetterService.update(
            db, cl.id, user.id,
            CoverLetterUpdate(content="Dear Hiring Manager,\nI am applying for the role at Acme.\nSincerely,\nAlice"),
        )
        db.commit()
        db.refresh(cl)
        return cl

    def test_diff_returns_computed_changes(self, client, test_user, db_session):
        user, headers = test_user
        cl = self._seed_versions(db_session, user)
        r = client.get(
            f"/api/cover-letter/{cl.id}/diff?from_version=1&to_version=2",
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["cover_letter_id"] == cl.id
        assert data["from_version"] == 1
        assert data["to_version"] == 2
        assert data["word_count_delta"] == 2  # "at Acme" added = two words
        assert len(data["changes"]) == 1
        assert data["changes"][0]["type"] == "replace"

    def test_diff_reversed_swaps_roles(self, client, test_user, db_session):
        user, headers = test_user
        cl = self._seed_versions(db_session, user)
        r = client.get(
            f"/api/cover-letter/{cl.id}/diff?from_version=2&to_version=1",
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["word_count_delta"] == -2

    def test_diff_rejects_same_version(self, client, test_user, db_session):
        user, headers = test_user
        cl = self._seed_versions(db_session, user)
        r = client.get(
            f"/api/cover-letter/{cl.id}/diff?from_version=1&to_version=1",
            headers=headers,
        )
        assert r.status_code == 400

    def test_diff_rejects_unknown_version(self, client, test_user, db_session):
        user, headers = test_user
        cl = self._seed_versions(db_session, user)
        r = client.get(
            f"/api/cover-letter/{cl.id}/diff?from_version=1&to_version=99",
            headers=headers,
        )
        assert r.status_code == 404

    def test_diff_requires_auth(self, client, db_session):
        user = _create_user(db_session)
        cl = self._seed_versions(db_session, user)
        r = client.get(
            f"/api/cover-letter/{cl.id}/diff?from_version=1&to_version=2",
        )
        assert r.status_code == 401

    # -- Generation metadata + coverage on save path ------------------------

    def test_generate_response_carries_metadata_and_coverage(self, client, test_user, db_session, monkeypatch):
        """POST /{id}/generate persists real provider metadata and returns coverage."""
        user, headers = test_user
        cl = _create_cover_letter(db_session, user.id)

        class FakeProvider:
            model_name = "gemini-test-model"

            def _generate_content(self, prompt):
                return "New letter mentioning Python and Docker."

        from app.routers.cover_letter import _get_ai_provider
        monkeypatch.setattr("app.routers.cover_letter._get_ai_provider", lambda: FakeProvider())

        r = client.post(
            f"/api/cover-letter/{cl.id}/generate",
            json={
                "resume_id": cl.resume_id,
                "job_title": "Software Engineer",
                "company_name": "Acme",
                "job_description": "Python Docker Kubernetes",
                "tone": "professional",
            },
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ai_provider"] == "Fake"
        assert data["model_name"] == "gemini-test-model"
        assert data["generated_at"] is not None
        assert data["content"] == "New letter mentioning Python and Docker."
        assert data["ats_coverage"]["covered_count"] == 2
        assert data["ats_coverage"]["total_keywords"] == 3
        assert data["version"] == 2

        # Metadata persisted on the row, not just in the response.
        db_session.expire_all()
        from app.models.cover_letter import CoverLetter
        persisted = db_session.query(CoverLetter).filter_by(id=cl.id).first()
        assert persisted.ai_provider == "Fake"
        assert persisted.model_name == "gemini-test-model"
        assert persisted.generated_at is not None

    def test_detail_includes_ats_coverage(self, client, test_user, db_session):
        user, headers = test_user
        cl = _create_cover_letter(db_session, user.id, content="Python and Docker experience.")
        r = client.get(f"/api/cover-letter/{cl.id}", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["ats_coverage"]["covered_count"] == 2
        assert data["ats_coverage"]["label"] == "2 of 3 keywords present"
