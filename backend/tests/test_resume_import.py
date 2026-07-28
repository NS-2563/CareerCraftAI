"""Tests for Phase 2E — Import Review UI backend endpoint.

Tests cover:
- Authentication is required
- Invalid file types are rejected
- Valid PDF parsing returns correct structure
- Response contains parsed_data, source_meta, resume_name, ai_used
- No database record is created
- Empty/no-text PDF is handled gracefully
- Sensitive data not exposed in logs
"""
import os
import json
import logging
from unittest.mock import patch, MagicMock, ANY

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.resume import ResumeCreate


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def db_session():
    """Provide a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

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
    """Create a test user."""
    from app.dependencies import get_password_hash
    user = User(
        email="importtest@example.com",
        username="importtest",
        hashed_password=get_password_hash("SecurePass123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for the test user."""
    from app.dependencies import create_access_token
    token = create_access_token({"sub": str(test_user.id), "ver": 0})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db_session, test_user):
    """Create a test client with overridden dependencies."""

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# =========================================================================
# Minimal PDF content (valid structure)
# =========================================================================

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 24 Tf 100 700 Td(Hello World)Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n..."
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n220\n%%EOF"
)


# =========================================================================
# Tests
# =========================================================================

class TestAuthentication:

    def test_requires_auth(self, db_session):
        """Verify the endpoint returns 401 without authentication."""

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as unauth:
                response = unauth.post(
                    "/api/resume/import/parse",
                    files={"file": ("test.pdf", MINIMAL_PDF, "application/pdf")},
                )
        finally:
            del app.dependency_overrides[get_db]

        assert response.status_code == 401

    def test_requires_active_user(self, client, auth_headers, db_session):
        """Verify an inactive user is rejected."""
        from fastapi import HTTPException

        def override_inactive():
            raise HTTPException(status_code=400, detail="Inactive user")

        app.dependency_overrides[get_current_active_user] = override_inactive
        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("test.pdf", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestFileValidation:

    def test_rejects_non_pdf(self, client, auth_headers):
        """Verify non-PDF files are rejected."""
        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("resume.txt", b"not a pdf content", "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_rejects_empty_filename(self, client, auth_headers):
        """Verify upload with no filename is handled."""
        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )
        # Should either work (default name) or fail gracefully
        assert response.status_code in (200, 422)


class TestParsing:

    @patch("app.routers.resume_import.extract_text_from_pdf")
    @patch("app.routers.resume_import.parse_resume_full")
    def test_successful_parse(self, mock_pipeline, mock_extract, client, auth_headers):
        """Verify a successful parse returns the expected structure."""
        mock_extract.return_value = "John Doe\nSoftware Engineer\nExperience\nCompany XYZ"

        mock_pipeline.return_value = {
            "parsed_data": {
                "personal": {"firstName": "John", "lastName": "Doe", "email": "john@example.com"},
                "summary": "Experienced engineer",
                "experience": [{"company": "XYZ Corp", "position": "Engineer"}],
                "education": [],
                "skills": [{"name": "Python", "category": ""}],
                "projects": [],
                "certifications": [],
                "languages": [],
                "interests": [],
                "references": [],
            },
            "source_meta": {
                "personal": {"ai_success": True, "sources": {"firstName": "rule", "email": "ai"}},
                "summary": {"ai_success": False, "sources": {"_all": "rule"}},
                "experience": {"ai_success": True, "sources": {"entry_0_company": "rule"}},
            },
            "ai_used": True,
            "deterministic": {},
        }

        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("resume.pdf", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "parsed_data" in data
        assert "source_meta" in data
        assert "resume_name" in data
        assert "ai_used" in data

        assert data["parsed_data"]["personal"]["firstName"] == "John"
        assert data["parsed_data"]["personal"]["email"] == "john@example.com"
        assert data["parsed_data"]["summary"] == "Experienced engineer"
        assert len(data["parsed_data"]["experience"]) == 1
        assert data["parsed_data"]["experience"][0]["company"] == "XYZ Corp"

        assert data["source_meta"]["personal"]["ai_success"] is True
        assert data["source_meta"]["summary"]["ai_success"] is False
        assert data["ai_used"] is True
        assert "Imported - resume" in data["resume_name"]

    @patch("app.routers.resume_import.extract_text_from_pdf")
    @patch("app.routers.resume_import.parse_resume_full")
    def test_no_db_record_created(self, mock_pipeline, mock_extract, client, auth_headers, db_session):
        """Verify the endpoint does NOT create a database record."""
        mock_extract.return_value = "John Doe\nSkills\nPython, React"
        mock_pipeline.return_value = {
            "parsed_data": {"personal": {"firstName": "John"}, "summary": "", "experience": [], "education": [],
                            "skills": [{"name": "Python"}], "projects": [], "certifications": [],
                            "languages": [], "interests": [], "references": []},
            "source_meta": {},
            "ai_used": False,
            "deterministic": {},
        }

        from app.models.resume import Resume
        count_before = db_session.query(Resume).count()

        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("resume.pdf", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )

        count_after = db_session.query(Resume).count()
        assert response.status_code == 200
        assert count_after == count_before, "No resume record should be created by the parse endpoint"

    @patch("app.routers.resume_import.extract_text_from_pdf")
    @patch("app.routers.resume_import.parse_resume_full")
    def test_ai_fallback_deterministic(self, mock_pipeline, mock_extract, client, auth_headers):
        """Verify response works when AI enrichment falls back."""
        mock_extract.return_value = "Jane Smith\nSkills\nJava, SQL"
        mock_pipeline.return_value = {
            "parsed_data": {"personal": {"firstName": "Jane", "lastName": "Smith"}, "summary": "", "experience": [],
                            "education": [], "skills": [{"name": "Java"}, {"name": "SQL"}], "projects": [],
                            "certifications": [], "languages": [], "interests": [], "references": []},
            "source_meta": {},
            "ai_used": False,
            "deterministic": {},
        }

        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("resume.pdf", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["parsed_data"]["personal"]["firstName"] == "Jane"
        assert len(data["parsed_data"]["skills"]) == 2

    @patch("app.routers.resume_import.extract_text_from_pdf")
    def test_empty_text_returns_error(self, mock_extract, client, auth_headers):
        """Verify empty/no-text PDF returns an error."""
        mock_extract.return_value = ""

        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("blank.pdf", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == 422
        assert "No extractable text" in response.text

    @patch("app.routers.resume_import.extract_text_from_pdf")
    def test_whitespace_only_text_returns_error(self, mock_extract, client, auth_headers):
        """Verify whitespace-only text returns an error."""
        mock_extract.return_value = "   \n  \t  "

        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("empty.pdf", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == 422
        assert "No extractable text" in response.text

    @patch("app.routers.resume_import.extract_text_from_pdf")
    @patch("app.routers.resume_import.parse_resume_full")
    def test_full_response_structure(self, mock_pipeline, mock_extract, client, auth_headers):
        """Verify all required response fields are present."""
        mock_extract.return_value = "Test Resume"
        mock_pipeline.return_value = {
            "parsed_data": {"personal": {}, "summary": "", "experience": [], "education": [],
                            "skills": [], "projects": [], "certifications": [],
                            "languages": [], "interests": [], "references": []},
            "source_meta": {},
            "ai_used": True,
            "deterministic": {},
        }

        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("test.pdf", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "parsed_data" in data
        assert "source_meta" in data
        assert "resume_name" in data
        assert "ai_used" in data

        assert isinstance(data["parsed_data"], dict)
        assert isinstance(data["source_meta"], dict)
        assert isinstance(data["resume_name"], str)
        assert isinstance(data["ai_used"], bool)

    @patch("app.routers.resume_import.extract_text_from_pdf")
    @patch("app.routers.resume_import.parse_resume_full")
    def test_filename_generates_name(self, mock_pipeline, mock_extract, client, auth_headers):
        """Verify resume_name is derived from the filename."""
        mock_extract.return_value = "Resume Content"
        mock_pipeline.return_value = {
            "parsed_data": {"personal": {}, "summary": "", "experience": [], "education": [],
                            "skills": [], "projects": [], "certifications": [],
                            "languages": [], "interests": [], "references": []},
            "source_meta": {},
            "ai_used": False,
            "deterministic": {},
        }

        response = client.post(
            "/api/resume/import/parse",
            files={"file": ("My_Senior_Resume.pdf", MINIMAL_PDF, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "My_Senior_Resume" in response.json()["resume_name"]


class TestLogging:

    def test_no_raw_content_in_logs(self, client, auth_headers, caplog):
        """Verify raw resume content is not logged."""
        caplog.set_level(logging.INFO)

        with patch("app.routers.resume_import.extract_text_from_pdf") as mock_extract:
            mock_extract.return_value = "Sensitive PII Data: john@email.com, 555-1234"
            with patch("app.routers.resume_import.parse_resume_full") as mock_pipeline:
                mock_pipeline.return_value = {
                    "parsed_data": {"personal": {"email": "john@email.com"}, "summary": "", "experience": [],
                                    "education": [], "skills": [], "projects": [], "certifications": [],
                                    "languages": [], "interests": [], "references": []},
                    "source_meta": {},
                    "ai_used": False,
                    "deterministic": {},
                }

                response = client.post(
                    "/api/resume/import/parse",
                    files={"file": ("test.pdf", MINIMAL_PDF, "application/pdf")},
                    headers=auth_headers,
                )

        assert response.status_code == 200
        log_text = "\n".join(caplog.messages)
        assert "john@email.com" not in log_text
        assert "555-1234" not in log_text
        assert "Sensitive PII" not in log_text
