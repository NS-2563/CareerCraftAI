"""Tests for P1-002 — Rate-Limit Tightening.

Tests cover:
- _user_or_ip_key extracts user:ID from valid JWT
- _user_or_ip_key falls back to IP for missing/invalid JWT
- 429 returned when rate limit is exceeded
"""
from unittest.mock import MagicMock

import pytest
from fastapi import Request
from starlette.testclient import TestClient

from app.main import app, _user_or_ip_key
from app.database import Base, get_db
from app.dependencies import get_current_active_user, create_access_token
from app.models.user import User


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def db_session():
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
    user = User(
        email="ratelimit_test@example.com",
        username="ratelimit_test",
        hashed_password="$2b$12$abcdefghijklmnopqrstuvwx",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user, db_session):
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def _override_get_db(db_session):
    def _get_db():
        yield db_session
    return _get_db


def _override_get_current_user(test_user):
    def _get_current_user():
        return test_user
    return _get_current_user


# =========================================================================
# Tests: _user_or_ip_key
# =========================================================================

def test_key_function_extracts_user_id_from_valid_jwt(test_user):
    token = create_access_token(data={"sub": str(test_user.id)})
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": f"Bearer {token}"}
    mock_request.client = MagicMock(host="1.2.3.4")

    key = _user_or_ip_key(mock_request)
    assert key == f"user:{test_user.id}"


def test_key_function_falls_back_to_ip_on_missing_auth():
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.client = MagicMock(host="5.6.7.8")

    key = _user_or_ip_key(mock_request)
    assert key == "5.6.7.8"


def test_key_function_falls_back_to_ip_on_invalid_token():
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": "Bearer invalid.token.here"}
    mock_request.client = MagicMock(host="9.10.11.12")

    key = _user_or_ip_key(mock_request)
    assert key == "9.10.11.12"


def test_key_function_falls_back_to_ip_on_bearer_no_token():
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": "Bearer "}
    mock_request.client = MagicMock(host="13.14.15.16")

    key = _user_or_ip_key(mock_request)
    assert key == "13.14.15.16"


# =========================================================================
# Tests: 429 enforcement
# =========================================================================

def test_rate_limit_429_returned_when_exceeded(db_session, test_user, auth_headers):
    """Send enough requests to trigger the 60/min limit and verify 429."""
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = _override_get_current_user(test_user)
    client = TestClient(app)
    try:
        last_resp = None
        for _ in range(70):
            last_resp = client.post(
                "/api/jd-match/analyze",
                json={"jd_text": "test", "resume_data": {"personal": {}}},
                headers=auth_headers,
            )
            if last_resp.status_code == 429:
                break

        assert last_resp is not None and last_resp.status_code == 429, (
            f"Expected eventual 429, last status: {last_resp.status_code if last_resp else 'N/A'}"
        )
    finally:
        app.dependency_overrides.clear()
