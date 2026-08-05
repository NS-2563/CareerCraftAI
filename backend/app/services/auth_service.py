import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger("audit.auth")
from app.models.user import User
from app.dependencies import (
    get_password_hash,
    verify_password,
    is_legacy_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.user import Token, UserCreate, UserResponse
from app.utils.exceptions import (
    NotFoundException,
    ConflictException,
    UnauthorizedException,
    TooManyRequestsException,
    AppException,
)


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def register(db: Session, user_data: UserCreate) -> tuple[User, Token]:
        """Register a new user."""
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        existing_username = db.query(User).filter(User.username == user_data.username).first()

        if existing_user or existing_username:
            raise ConflictException("An account with this email or username already exists")

        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            token_version=0,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        token = AuthService._create_tokens(db_user.id, db_user.token_version)

        logger.info("REGISTER user_id=%s email=%s", db_user.id, db_user.email)

        return db_user, token

    @staticmethod
    def login(db: Session, email: str, password: str) -> tuple[User, Token]:
        """Authenticate and login user."""
        user = db.query(User).filter(User.email == email).first()

        if user and user.locked_until and user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None):
            raise TooManyRequestsException("Account is temporarily locked. Try again later.")

        if not user or not verify_password(password, user.hashed_password if user else ""):
            if user:
                user.failed_login_attempts += 1
                locked = user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS
                if locked:
                    user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
                        minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                    )
                db.commit()
                logger.warning(
                    "LOGIN_FAILED user_id=%s email=%s attempt=%s locked=%s",
                    user.id, email, user.failed_login_attempts, locked,
                )
            raise UnauthorizedException("Invalid email or password")

        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

        if not user.is_active:
            raise UnauthorizedException("User account is disabled")

        if is_legacy_hash(user.hashed_password):
            user.hashed_password = get_password_hash(password)
            logger.info("LEGACY_UPGRADE user_id=%s email=%s", user.id, email)
            db.commit()

        token = AuthService._create_tokens(user.id, user.token_version)

        logger.info("LOGIN_OK user_id=%s email=%s", user.id, email)

        return user, token

    @staticmethod
    def refresh_token(db: Session, refresh_token_value: str) -> Token:
        """Refresh access token using refresh token (with rotation).

        Validates the refresh token, checks token version, increments the
        user's token version (invalidating the old token), and issues a
        new token pair.
        """
        payload = decode_token(refresh_token_value)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise UnauthorizedException("User not found")

        if not user.is_active:
            raise UnauthorizedException("User account is disabled")

        token_ver = payload.get("ver", 0)
        if token_ver != user.token_version:
            raise UnauthorizedException("Refresh token has been revoked")

        user.token_version += 1
        db.commit()

        token = AuthService._create_tokens(user.id, user.token_version)

        logger.info("REFRESH user_id=%s new_version=%s", user.id, user.token_version)

        return token

    @staticmethod
    def logout(user: User, db: Session) -> None:
        """Logout user by incrementing token version server-side."""
        user.token_version += 1
        db.commit()
        logger.info("LOGOUT user_id=%s new_version=%s", user.id, user.token_version)

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change the user's password and revoke every existing session.

        The token version is incremented so all previously issued tokens
        (including the current one) are invalidated server-side.
        """
        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedException("Current password is incorrect")

        user.hashed_password = get_password_hash(new_password)
        user.token_version += 1
        db.commit()
        logger.info("CHANGE_PASSWORD user_id=%s new_version=%s", user.id, user.token_version)

    @staticmethod
    def _create_tokens(user_id: int, token_version: int = 0) -> Token:
        """Create access and refresh tokens."""
        access_token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            token_version=token_version,
        )
        refresh_token_value = create_refresh_token(
            data={"sub": str(user_id)},
            token_version=token_version,
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token_value,
            token_type="bearer",
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("User", str(user_id))
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise NotFoundException("User", email)
        return user


# Google OAuth placeholder functions
class GoogleOAuthService:
    """Service for Google OAuth operations (placeholder)."""

    @staticmethod
    def get_authorization_url() -> str:
        """Get Google OAuth authorization URL."""
        # Placeholder - would implement actual Google OAuth
        raise NotImplementedError("Google OAuth not yet implemented")

    @staticmethod
    def exchange_code(code: str, db: Session) -> tuple[User, Token]:
        """Exchange authorization code for tokens."""
        # Placeholder - would implement actual Google OAuth
        raise NotImplementedError("Google OAuth not yet implemented")

    @staticmethod
    def get_user_info(access_token: str) -> dict:
        """Get user info from Google."""
        # Placeholder - would implement actual Google OAuth
        raise NotImplementedError("Google OAuth not yet implemented")