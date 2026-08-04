"""Per-application conversation status resolution.

The effective conversation status of a job application is ALWAYS derivable from
real data — never stored as a standalone manual-only value that could silently
drift from what the timeline actually shows. It is a pure function of:

  * the **last message's ``direction``** ("Needs Reply" when inbound, "Waiting"
    when outbound), and
  * the linked ``JobApplication.status`` (auto-closes the conversation).

A single nullable ``job_applications.conversation_status_override`` column lets
the user explicitly force a state, but it only surfaces when the application is
NOT in a terminal pipeline state.

Precedence rule (highest first):
  1. TERMINAL APPLICATION STATUS → "closed"
     An application in {Accepted, Rejected, Withdrawn} is over. Its conversation
     is always shown as Closed — even if the user had manually set
     "needs_reply". The manual override is NOT deleted; it is merely masked, so
     if the application is later re-opened (moved back to a non-terminal
     status) the user's explicit choice is restored.
  2. MANUAL OVERRIDE → respected
     An explicit user choice ("closed", "needs_reply", or "waiting") wins over
     whatever the last message direction would otherwise derive. This is what
     makes "Mark conversation closed" / "Reopen" sticky across new messages.
  3. DERIVED FROM LAST MESSAGE DIRECTION
     inbound → "needs_reply" | outbound → "waiting" | no messages → None.
"""

from typing import Optional, Set

from sqlalchemy.orm import Session

from app.communication.models import CommunicationMessage
from app.models.job_application import JobApplication
from app.schemas.job_tracker import JobStatus

NEEDS_REPLY = "needs_reply"
WAITING = "waiting"
CLOSED = "closed"

VALID_CONVERSATION_STATUSES: Set[str] = {NEEDS_REPLY, WAITING, CLOSED}

# Application pipeline states that end the conversation for good. There is no
# "Offer declined" value in JobStatus; a declined offer maps onto Withdrawn or
# Rejected. Offer is intentionally NOT here — negotiation may still be ongoing.
TERMINAL_CONVERSATION_STATUSES: Set[JobStatus] = {
    JobStatus.ACCEPTED,
    JobStatus.REJECTED,
    JobStatus.WITHDRAWN,
}

# Why the status is what it is (surfaced in the API for transparency).
SOURCE_APPLICATION_STATUS = "application_status"
SOURCE_MANUAL = "manual"
SOURCE_DERIVED = "derived"
SOURCE_NONE = "none"


def derive_from_direction(last_direction: Optional[str]) -> Optional[str]:
    """Map the last message's direction to a conversation status.

    inbound -> "needs_reply", outbound -> "waiting", anything else -> None.
    """
    if last_direction == "inbound":
        return NEEDS_REPLY
    if last_direction == "outbound":
        return WAITING
    return None


def resolve_status(
    job: JobApplication,
    last_message: Optional[CommunicationMessage],
):
    """Resolve (status, source) for an application. status may be None.

    Pure and deterministic — see module docstring for the precedence rule.
    """
    if job.status in TERMINAL_CONVERSATION_STATUSES:
        return CLOSED, SOURCE_APPLICATION_STATUS
    if job.conversation_status_override in VALID_CONVERSATION_STATUSES:
        return job.conversation_status_override, SOURCE_MANUAL
    if last_message is not None:
        return derive_from_direction(last_message.direction), SOURCE_DERIVED
    return None, SOURCE_NONE


def get_last_message(
    db: Session,
    user_id: int,
    job_application_id: int,
) -> Optional[CommunicationMessage]:
    """Most recent message (created_at desc, id desc tiebreaker) for an app."""
    return (
        db.query(CommunicationMessage)
        .filter(
            CommunicationMessage.user_id == user_id,
            CommunicationMessage.related_job_application_id == job_application_id,
        )
        .order_by(
            CommunicationMessage.created_at.desc(),
            CommunicationMessage.id.desc(),
        )
        .first()
    )


def _last_message_map(db: Session, user_id: int, job_ids) -> dict:
    """One-query map of job_application_id -> last message for many jobs."""
    if not job_ids:
        return {}
    messages = (
        db.query(CommunicationMessage)
        .filter(
            CommunicationMessage.user_id == user_id,
            CommunicationMessage.related_job_application_id.in_(job_ids),
        )
        .order_by(
            CommunicationMessage.created_at.desc(),
            CommunicationMessage.id.desc(),
        )
        .all()
    )
    last_by_job = {}
    for message in messages:
        last_by_job.setdefault(message.related_job_application_id, message)
    return last_by_job


def build_status_response(
    job: JobApplication,
    last_message: Optional[CommunicationMessage],
) -> dict:
    """Serialize one application's resolved conversation status."""
    status, source = resolve_status(job, last_message)
    return {
        "job_application_id": job.id,
        "status": status,
        "source": source,
        "application_status": _job_status_value(job),
        "last_message_direction": last_message.direction if last_message else None,
    }


def _job_status_value(job: JobApplication) -> str:
    if isinstance(job.status, JobStatus):
        return job.status.value
    return str(job.status)
