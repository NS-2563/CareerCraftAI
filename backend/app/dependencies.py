import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token"
)

_BCRYPT_VERSION = "$2b$"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Supports both bcrypt (current) and legacy SHA256+static-salt hashes
    so that existing users can still log in during the migration period.
    """
    if is_legacy_hash(hashed_password):
        hash_obj = hashlib.sha256()
        hash_obj.update((plain_password.encode() + b"careercraft_salt_2024"))
        return hash_obj.hexdigest() == hashed_password
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def is_legacy_hash(hashed_password: str) -> bool:
    """Check if a password hash uses the legacy SHA256 format."""
    return not hashed_password.startswith(_BCRYPT_VERSION)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    token_version: int = 0,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access", "ver": token_version})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, token_version: int = 0) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "ver": token_version})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def _resolve_user(payload: dict, db: Session) -> Optional[User]:
    """Resolve a User from a verified JWT payload, or None.

    Returns None when the token has no subject, the user does not exist,
    or the token version does not match the user's current ``token_version``.
    """
    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        return None

    token_ver = payload.get("ver", 0)
    if token_ver != user.token_version:
        return None

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_revoked_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has been revoked",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user = _resolve_user(payload, db)
    if user is not None:
        return user

    # Distinguish a revoked token (subject + user exist, version mismatch)
    # from outright invalid credentials, matching the pre-refactor behavior.
    if payload.get("sub") is not None and db.query(User).filter(
        User.id == int(payload["sub"])
    ).first() is not None:
        raise token_revoked_exception
    raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user, but returns None instead of raising on missing/invalid token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ")

    payload = decode_token(token)
    if payload is None:
        return None

    user = _resolve_user(payload, db)
    if user is None:
        return None

    if not user.is_active:
        return None

    return user