"""Rate-limit configuration.

Extracted from ``app.main`` so that routers can import ``limiter`` without
creating a circular import (``app.main`` imports every router, and every
router imported ``limiter`` from ``app.main``).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.dependencies import decode_token


def _user_or_ip_key(request) -> str:
    """Extract user ID from the request's JWT if available, else fall back to IP.

    This allows AI-calling endpoints (which require authentication) to be
    rate-limited per user rather than per IP, while unauthenticated auth
    endpoints fall back to IP-based limiting automatically.
    """
    try:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            payload = decode_token(token)
            user_id = payload.get("sub") if payload else None
            if user_id is not None:
                return f"user:{user_id}"
    except Exception:
        pass
    return get_remote_address(request)


limiter = Limiter(key_func=_user_or_ip_key)
