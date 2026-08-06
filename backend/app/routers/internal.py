"""Internal, machine-to-machine endpoints.

These endpoints are NOT reachable by normal user JWT auth. They are protected
by a shared-secret header and are intended to be called only by an external
scheduler — Render's Cron Jobs or a scheduled GitHub Actions workflow making
an authenticated HTTP request. Regular users have no legitimate reason to call
them, and they are deliberately not part of the normal user-facing API.
"""

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.communication.suggestions_service import check_and_create_suggestions
from app.database import get_db
from app.utils.response import success_response

router = APIRouter(prefix="/api/internal", tags=["Internal"])

INTERNAL_SECRET_HEADER = "X-Internal-Secret"


def _verify_internal_secret(x_internal_secret: str) -> None:
    """Fail closed unless the request carries the configured shared secret.

    Comparison uses hmac.compare_digest for constant-time behavior. An empty
    configured secret means the operator has not set up the job trigger yet, so
    the endpoint returns 503 (misconfiguration) rather than running
    unauthenticated.
    """
    configured = settings.INTERNAL_JOB_SECRET
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "Internal job secret is not configured"},
        )
    if not x_internal_secret or not hmac.compare_digest(
        x_internal_secret.encode("utf-8"), configured.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or missing internal secret"},
        )


@router.post("/run-daily-suggestions", status_code=status.HTTP_200_OK)
def run_daily_suggestions(
    x_internal_secret: str = Header(None, alias=INTERNAL_SECRET_HEADER),
    db: Session = Depends(get_db),
):
    """Run the daily Communication follow-up-suggestion check.

    Intended to be called ONCE per day by an external scheduler — either
    Render's Cron Jobs or a scheduled GitHub Actions workflow — sending the
    configured INTERNAL_JOB_SECRET in the X-Internal-Secret header. This is the
    single trigger for the job: the in-process APScheduler registration that
    previously ran inside the web process was removed, so there is exactly one
    way this job runs (never duplicated across instances, never skipped because
    the host slept).

    Runs the same ``check_and_create_suggestions`` logic the old scheduler job
    called; identical behavior. Errors propagate as 5xx so the external
    scheduler can retry or alert.
    """
    _verify_internal_secret(x_internal_secret)
    count = check_and_create_suggestions(db)
    return success_response(
        data={"suggestions_created": count},
        message="Daily suggestion check complete",
    )
