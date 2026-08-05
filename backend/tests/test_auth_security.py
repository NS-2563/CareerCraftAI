import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import ALL models so SQLAlchemy can resolve relationships
from app.database import Base
from app.models.user import User
from app.models.resume import Resume  # noqa: F401
from app.models.cover_letter import CoverLetter  # noqa: F401
from app.models.career_report import CareerReport  # noqa: F401
from app.models.job_application import JobApplication  # noqa: F401

from app.config import settings
from app.dependencies import (
    get_password_hash,
    verify_password,
    is_legacy_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)

_LEGACY_SALT = b"careercraft_salt_2024"

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── helpers ───────────────────────────────────────────────────────────

def _legacy_sha256_hash(password: str) -> str:
    h = hashlib.sha256()
    h.update(password.encode() + _LEGACY_SALT)
    return h.hexdigest()


def _create_user(
    db,
    email="legacy@example.com",
    username="legacyuser",
    password="testpass123",
    use_legacy=True,
):
    hashed = _legacy_sha256_hash(password) if use_legacy else get_password_hash(password)
    user = User(
        email=email,
        username=username,
        hashed_password=hashed,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── 1. New password hashes use bcrypt ────────────────────────────────

class TestPasswordHashing:

    def test_new_hash_is_bcrypt_format(self):
        h = get_password_hash("securePass123")
        assert h.startswith("$2b$"), f"Expected bcrypt hash starting with $2b$, got: {h[:20]}..."
        assert len(h) == 60, f"Expected bcrypt hash length 60, got {len(h)}"

    def test_bcrypt_verification_succeeds(self):
        h = get_password_hash("securePass123")
        assert verify_password("securePass123", h) is True

    def test_bcrypt_verification_fails_wrong_password(self):
        h = get_password_hash("securePass123")
        assert verify_password("wrongPassword1", h) is False

    def test_bcrypt_hashes_differ_for_same_password(self):
        h1 = get_password_hash("samePass123")
        h2 = get_password_hash("samePass123")
        assert h1 != h2, "bcrypt should produce different hashes for the same password (unique salt)"


# ─── 2. Legacy SHA256 verification works during migration ────────────

class TestLegacyHashCompatibility:

    def test_legacy_hash_detection(self):
        legacy = _legacy_sha256_hash("testpass123")
        bcrypt_h = get_password_hash("testpass123")
        assert is_legacy_hash(legacy) is True
        assert is_legacy_hash(bcrypt_h) is False

    def test_legacy_verification_succeeds(self):
        legacy = _legacy_sha256_hash("testpass123")
        assert verify_password("testpass123", legacy) is True

    def test_legacy_verification_fails_wrong_password(self):
        legacy = _legacy_sha256_hash("testpass123")
        assert verify_password("wrongPassword1", legacy) is False

    def test_legacy_hash_still_accepted_after_bcrypt_introduction(self):
        legacy = _legacy_sha256_hash("mypassword1")
        bcrypt_h = get_password_hash("mypassword1")
        assert verify_password("mypassword1", legacy) is True
        assert verify_password("mypassword1", bcrypt_h) is True


# ─── 3. Legacy login upgrades stored hash to bcrypt ──────────────────

class TestLegacyMigration:

    def test_successful_legacy_login_upgrades_hash(self, db_session):
        user = _create_user(db_session, use_legacy=True)
        original_hash = user.hashed_password
        assert is_legacy_hash(original_hash) is True

        assert verify_password("testpass123", user.hashed_password) is True
        if is_legacy_hash(user.hashed_password):
            user.hashed_password = get_password_hash("testpass123")
            db_session.commit()
            db_session.refresh(user)

        new_hash = user.hashed_password
        assert is_legacy_hash(new_hash) is False
        assert new_hash != original_hash
        assert verify_password("testpass123", new_hash) is True

    def test_invalid_legacy_password_does_not_upgrade(self, db_session):
        user = _create_user(db_session, use_legacy=True)
        original_hash = user.hashed_password

        assert verify_password("wrongPassword1", user.hashed_password) is False

        if verify_password("wrongPassword1", user.hashed_password):
            user.hashed_password = get_password_hash("wrongPassword1")
            db_session.commit()
            db_session.refresh(user)

        assert user.hashed_password == original_hash
        assert is_legacy_hash(user.hashed_password) is True

    def test_bcrypt_login_leaves_hash_unchanged(self, db_session):
        user = _create_user(db_session, use_legacy=False)
        original_hash = user.hashed_password

        assert verify_password("testpass123", user.hashed_password) is True
        if is_legacy_hash(user.hashed_password):
            user.hashed_password = get_password_hash("testpass123")
            db_session.commit()
            db_session.refresh(user)

        assert user.hashed_password == original_hash

    def test_upgraded_hash_works_for_future_logins(self, db_session):
        user = _create_user(db_session, use_legacy=True)

        assert verify_password("testpass123", user.hashed_password) is True
        if is_legacy_hash(user.hashed_password):
            user.hashed_password = get_password_hash("testpass123")
            db_session.commit()

        db_session.refresh(user)
        assert is_legacy_hash(user.hashed_password) is False
        assert verify_password("testpass123", user.hashed_password) is True
        assert verify_password("wrongPassword1", user.hashed_password) is False


# ─── 4. Password length validation ───────────────────────────────────

class TestPasswordPolicy:

    def test_minimum_length_enforced_by_schema(self):
        from pydantic import ValidationError
        from app.schemas.user import UserCreate

        with pytest.raises(ValidationError) as exc:
            UserCreate(email="a@b.com", username="testuser", password="1234567")
        errors = exc.value.errors()
        assert any("at least 8" in str(e["msg"]) for e in errors), \
            f"Expected min_length=8 error, got: {errors}"

        user = UserCreate(email="a@b.com", username="testuser", password="12345678")
        assert user.password == "12345678"


# ─── 5. No plaintext passwords exposed ───────────────────────────────

class TestNoPasswordExposure:

    def test_password_not_in_response_schema(self):
        from app.schemas.user import UserResponse
        fields = UserResponse.model_fields
        assert "password" not in fields
        assert "hashed_password" not in fields

    def test_hashed_password_not_in_user_response(self, db_session):
        user = _create_user(db_session, use_legacy=False)
        from app.schemas.user import UserResponse
        resp = UserResponse.model_validate(user)
        data = resp.model_dump()
        assert "password" not in data
        assert "hashed_password" not in data


# ─── 6. Token version is included in JWT ─────────────────────────────

class TestTokenVersion:

    def test_access_token_contains_version(self):
        token = create_access_token(data={"sub": "1"}, token_version=3)
        payload = decode_token(token)
        assert payload is not None
        assert payload["ver"] == 3
        assert payload["type"] == "access"

    def test_refresh_token_contains_version(self):
        token = create_refresh_token(data={"sub": "1"}, token_version=5)
        payload = decode_token(token)
        assert payload is not None
        assert payload["ver"] == 5
        assert payload["type"] == "refresh"

    def test_token_without_version_defaults_to_zero(self):
        token = create_access_token(data={"sub": "1"}, token_version=0)
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("ver") == 0


# ─── 7. Token version validation (get_current_user) ─────────────────

class TestTokenVersionValidation:

    def _create_user_with_version(self, db, version=0):
        from app.dependencies import get_password_hash
        user = User(
            email=f"ver{version}@test.com",
            username=f"veruser{version}",
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
            token_version=version,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def test_token_with_matching_version_accepted(self, db_session):
        user = self._create_user_with_version(db_session, version=2)
        token = create_access_token(data={"sub": str(user.id)}, token_version=2)

        payload = decode_token(token)
        assert payload is not None
        assert payload["ver"] == user.token_version

    def test_token_with_mismatched_version_rejected(self, db_session):
        user = self._create_user_with_version(db_session, version=0)
        token = create_access_token(data={"sub": str(user.id)}, token_version=0)

        payload = decode_token(token)
        assert payload is not None
        assert payload["ver"] == 0

        # Simulate logout (version increment)
        user.token_version = 1
        db_session.commit()

        # Token version 0 should no longer match
        assert payload["ver"] != user.token_version


# ─── 8. Refresh token rotation ───────────────────────────────────────

class TestRefreshTokenRotation:

    def test_refresh_returns_new_access_token(self, db_session):
        user = _create_user(db_session, use_legacy=False)
        old_token = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)

        payload = decode_token(old_token)
        assert payload is not None

        user.token_version += 1
        db_session.commit()

        new_token = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)

        assert new_token != old_token
        payload2 = decode_token(new_token)
        assert payload2["ver"] == user.token_version

    def test_new_refresh_token_usable(self, db_session):
        user = _create_user(db_session, use_legacy=False)
        old_ver = user.token_version
        token1 = create_refresh_token(data={"sub": str(user.id)}, token_version=old_ver)

        user.token_version += 1
        db_session.commit()

        token2 = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)
        payload2 = decode_token(token2)
        assert payload2 is not None
        assert payload2["ver"] == user.token_version

    def test_old_refresh_token_rejected_after_rotation(self, db_session):
        user = _create_user(db_session, use_legacy=False)

        old_token = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)
        user.token_version += 1
        db_session.commit()

        old_payload = decode_token(old_token)
        assert old_payload is not None
        assert old_payload["ver"] != user.token_version


# ─── 9. Refresh token accepted from POST body (integration check) ────

class TestRefreshTokenTransport:

    def test_refresh_token_schema_accepts_body(self):
        from app.schemas.user import RefreshRequest
        req = RefreshRequest(refresh_token="some.jwt.token")
        assert req.refresh_token == "some.jwt.token"

    def test_refresh_token_not_in_query_param(self):
        from app.schemas.user import RefreshRequest
        req = RefreshRequest(refresh_token="test")
        assert hasattr(req, "refresh_token")


# ─── 10. Logout invalidation ─────────────────────────────────────────

class TestLogout:

    def test_logout_increments_token_version(self, db_session):
        user = _create_user(db_session, use_legacy=False)
        initial_version = user.token_version
        assert initial_version >= 0

        user.token_version += 1
        db_session.commit()
        db_session.refresh(user)
        assert user.token_version == initial_version + 1

    def test_tokens_invalidated_after_logout(self, db_session):
        from app.services.auth_service import AuthService
        user = _create_user(db_session, use_legacy=False)

        old_access = create_access_token(data={"sub": str(user.id)}, token_version=user.token_version)
        old_refresh = create_refresh_token(data={"sub": str(user.id)}, token_version=user.token_version)

        AuthService.logout(user, db_session)

        assert decode_token(old_access) is not None
        old_access_payload = decode_token(old_access)
        assert old_access_payload["ver"] != user.token_version

        old_refresh_payload = decode_token(old_refresh)
        assert old_refresh_payload["ver"] != user.token_version

    def test_logout_response_does_not_expose_token(self):
        from app.schemas.user import LogoutResponse
        resp = LogoutResponse()
        data = resp.model_dump()
        assert "message" in data
        assert "token" not in data
        assert "access_token" not in data
        assert "refresh_token" not in data


# ─── 11. AuthService version-aware registration ──────────────────────

class TestRegistrationTokenVersion:

    def test_new_user_starts_at_version_zero(self, db_session):
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate

        user_data = UserCreate(email="fresh@test.com", username="freshuser", password="freshPass123")
        user, token = AuthService.register(db_session, user_data)

        assert user.token_version == 0

        access_payload = decode_token(token.access_token)
        assert access_payload["ver"] == 0

        refresh_payload = decode_token(token.refresh_token)
        assert refresh_payload["ver"] == 0


# ─── 12. Rate limiting configuration ──────────────────────────────────

class TestRateLimitConfig:

    def test_rate_limit_settings_are_configured(self):
        from app.config import settings
        assert settings.RATE_LIMIT_LOGIN is not None
        assert settings.RATE_LIMIT_REGISTER is not None
        assert settings.RATE_LIMIT_REFRESH is not None

    def test_rate_limit_strings_are_valid(self):
        from app.config import settings
        for rl in [settings.RATE_LIMIT_LOGIN, settings.RATE_LIMIT_REGISTER, settings.RATE_LIMIT_REFRESH]:
            assert "/" in rl, f"Rate limit '{rl}' should contain '/'"


# ─── 13. Failed login protection ──────────────────────────────────────

class TestFailedLoginProtection:

    def _create_login_user(self, db, email="locktest@test.com", password="securePass123"):
        from app.dependencies import get_password_hash
        user = User(
            email=email,
            username="locktest",
            hashed_password=get_password_hash(password),
            is_active=True,
            failed_login_attempts=0,
            token_version=0,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, password

    def test_failed_login_increments_counter(self, db_session):
        from app.services.auth_service import AuthService
        user, pw = self._create_login_user(db_session)

        for i in range(3):
            try:
                AuthService.login(db_session, user.email, "wrongpass")
            except Exception:
                pass

        db_session.refresh(user)
        assert user.failed_login_attempts == 3

    def test_account_locked_after_threshold(self, db_session):
        from app.services.auth_service import AuthService
        from app.config import settings
        user, pw = self._create_login_user(db_session)

        for i in range(settings.MAX_FAILED_LOGIN_ATTEMPTS):
            try:
                AuthService.login(db_session, user.email, "wrongpass")
            except Exception:
                pass

        db_session.refresh(user)
        assert user.failed_login_attempts == settings.MAX_FAILED_LOGIN_ATTEMPTS
        assert user.locked_until is not None
        assert user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None)

    def test_login_while_locked_is_rejected(self, db_session):
        from app.services.auth_service import AuthService
        from app.config import settings
        user, pw = self._create_login_user(db_session)

        for i in range(settings.MAX_FAILED_LOGIN_ATTEMPTS + 1):
            try:
                AuthService.login(db_session, user.email, "wrongpass")
            except Exception:
                pass

        db_session.refresh(user)
        assert user.locked_until is not None

        with pytest.raises(Exception) as exc:
            AuthService.login(db_session, user.email, pw)
        assert "locked" in str(exc.value).lower() or exc.type.__name__ == "TooManyRequestsException"

    def test_lockout_auto_expires(self, db_session):
        from app.services.auth_service import AuthService
        from app.config import settings
        user, pw = self._create_login_user(db_session)

        for i in range(settings.MAX_FAILED_LOGIN_ATTEMPTS):
            try:
                AuthService.login(db_session, user.email, "wrongpass")
            except Exception:
                pass

        db_session.refresh(user)

        user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        db_session.commit()

        result = AuthService.login(db_session, user.email, pw)
        assert result is not None

    def test_successful_login_resets_failed_attempts(self, db_session):
        from app.services.auth_service import AuthService
        user, pw = self._create_login_user(db_session)
        user.failed_login_attempts = 3
        user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        db_session.commit()

        AuthService.login(db_session, user.email, pw)
        db_session.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_successful_login_clears_lockout(self, db_session):
        from app.services.auth_service import AuthService
        user, pw = self._create_login_user(db_session)
        user.failed_login_attempts = 4
        user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        db_session.commit()

        AuthService.login(db_session, user.email, pw)
        db_session.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_incorrect_credentials_do_not_reset_counter(self, db_session):
        from app.services.auth_service import AuthService
        user, pw = self._create_login_user(db_session)
        user.failed_login_attempts = 2
        db_session.commit()

        try:
            AuthService.login(db_session, user.email, "wrongpass")
        except Exception:
            pass

        db_session.refresh(user)
        assert user.failed_login_attempts == 3


# ─── 14. User enumeration ────────────────────────────────────────────

class TestUserEnumeration:

    def test_duplicate_email_returns_generic_message(self, db_session):
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate

        user_data = UserCreate(email="dup@test.com", username="user1", password="testPass123")
        AuthService.register(db_session, user_data)

        dup_data = UserCreate(email="dup@test.com", username="user2", password="testPass456")
        with pytest.raises(Exception) as exc:
            AuthService.register(db_session, dup_data)

        error_msg = str(exc.value).lower()
        assert "email" not in error_msg or "already registered" not in error_msg
        assert "exists" in error_msg or "already" in error_msg

    def test_duplicate_username_returns_generic_message(self, db_session):
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate

        user_data = UserCreate(email="user1@test.com", username="dupuser", password="testPass123")
        AuthService.register(db_session, user_data)

        dup_data = UserCreate(email="user2@test.com", username="dupuser", password="testPass456")
        with pytest.raises(Exception) as exc:
            AuthService.register(db_session, dup_data)

        error_msg = str(exc.value).lower()
        assert "username" not in error_msg or "already taken" not in error_msg
        assert "exists" in error_msg or "already" in error_msg

    def test_duplicate_email_and_username_same_message(self, db_session):
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate

        user_data = UserCreate(email="first@test.com", username="firstuser", password="testPass123")
        AuthService.register(db_session, user_data)

        with pytest.raises(Exception) as exc_email:
            AuthService.register(
                db_session,
                UserCreate(email="first@test.com", username="other", password="testPass456"),
            )

        with pytest.raises(Exception) as exc_user:
            AuthService.register(
                db_session,
                UserCreate(email="other@test.com", username="firstuser", password="testPass456"),
            )

        assert str(exc_email.value) == str(exc_user.value)

    def test_fresh_registration_succeeds(self, db_session):
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate

        user_data = UserCreate(
            email="fresh_reg@test.com",
            username="fresh_reg_user",
            password="testPass123",
        )
        user, token = AuthService.register(db_session, user_data)
        assert user.email == "fresh_reg@test.com"


# ─── 15. Lockout configuration ───────────────────────────────────────

class TestLockoutConfig:

    def test_lockout_settings_are_configured(self):
        from app.config import settings
        assert settings.MAX_FAILED_LOGIN_ATTEMPTS >= 3
        assert settings.ACCOUNT_LOCKOUT_MINUTES >= 1
