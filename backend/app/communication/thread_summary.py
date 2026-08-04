"""Deterministic per-application thread-summary derivation.

The thread summary is ALWAYS a pure function of the real messages in an
application's thread — never a stored value that could drift from the timeline.
It computes:

  * ``last_reply``           — the most recent message (either direction), with
                               its sender and timestamp
  * ``last_recruiter_email`` — the most recent inbound message
  * ``response_overdue``     — a clearly-defined, single rule (see below)
  * ``state``                — a coarse, human label for the summary

Overdue rule (one documented, consistent threshold used everywhere):
  "Response overdue" is True when the most recent message in the thread is
  inbound (the ball is in the user's court) AND more than
  ``settings.COMMUNICATION_OVERDUE_AFTER_DAYS`` (default 5) whole days have
  passed since that inbound message was received with no outbound reply after
  it. Boundary: at exactly N days it is NOT yet overdue (the rule is strictly
  greater than N).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.communication.models import CommunicationMessage

# Human state label derived from the last message + overdue rule.
STATE_NONE = "none"
STATE_WAITING = "waiting"
STATE_NEEDS_REPLY = "needs_reply"
STATE_RESPONSE_OVERDUE = "response_overdue"

EMPTY_SUMMARY = {
    "has_thread": False,
    "last_reply": None,
    "last_recruiter_email": None,
    "last_message_direction": None,
    "response_overdue": False,
    "response_overdue_days": None,
    "state": STATE_NONE,
}


def _overdue_after_days() -> int:
    return int(getattr(settings, "COMMUNICATION_OVERDUE_AFTER_DAYS", 5))


def _as_utc(dt) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _whole_days_since(dt) -> Optional[int]:
    utc = _as_utc(dt)
    if utc is None:
        return None
    return max((datetime.now(timezone.utc) - utc).days, 0)


def _message_brief(message: CommunicationMessage) -> dict:
    return {
        "id": message.id,
        "direction": message.direction,
        "sender_name": message.sender_name,
        "sender_email": message.sender_email,
        "recipient_name": message.recipient_name,
        "message_type": message.message_type,
        "subject": message.subject,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def compute_thread_summary(messages: list) -> dict:
    """Compute the thread summary from a thread's messages (any order).

    Pure and deterministic: identical message rows always yield the same
    summary. Pass the full thread; only the most recent messages matter.
    """
    if not messages:
        return dict(EMPTY_SUMMARY)

    # Most recent message: created_at desc, id desc as a stable tiebreaker.
    last = max(messages, key=lambda m: (m.created_at or datetime.min, m.id))
    inbound = [m for m in messages if m.direction == "inbound"]
    last_inbound = max(
        inbound,
        key=lambda m: (m.created_at or datetime.min, m.id),
    ) if inbound else None

    last_direction = last.direction if last is not None else None

    response_overdue = False
    overdue_days = None
    if last_direction == "inbound":
        days = _whole_days_since(last.created_at)
        if days is not None and days > _overdue_after_days():
            response_overdue = True
            overdue_days = days

    if response_overdue:
        state = STATE_RESPONSE_OVERDUE
    elif last_direction == "inbound":
        state = STATE_NEEDS_REPLY
    elif last_direction == "outbound":
        state = STATE_WAITING
    else:
        state = STATE_NONE

    return {
        "has_thread": True,
        "last_reply": _message_brief(last),
        "last_recruiter_email": _message_brief(last_inbound) if last_inbound else None,
        "last_message_direction": last_direction,
        "response_overdue": response_overdue,
        "response_overdue_days": overdue_days,
        "state": state,
    }


def _thread_summary_map(db: Session, user_id: int, job_ids) -> dict:
    """One-query map of job_application_id -> summary for many applications."""
    if not job_ids:
        return {}
    messages = (
        db.query(CommunicationMessage)
        .filter(
            CommunicationMessage.user_id == user_id,
            CommunicationMessage.related_job_application_id.in_(job_ids),
        )
        .order_by(
            CommunicationMessage.created_at.asc(),
            CommunicationMessage.id.asc(),
        )
        .all()
    )
    by_job = {}
    for message in messages:
        by_job.setdefault(message.related_job_application_id, []).append(message)
    return {
        job_id: compute_thread_summary(msgs)
        for job_id, msgs in by_job.items()
    }


def attach_thread_summary(db: Session, messages: list) -> list:
    """Attach transient ``thread_summary`` to each message in a list.

    Works for a full thread (``get_thread``) or a cross-application slice
    (``list_messages``): summaries are computed over each application's FULL
    thread in one batch query, so a paginated message list never truncates the
    source data the summary is derived from.
    """
    if not messages:
        return messages
    user_id = messages[0].user_id
    job_ids = {
        m.related_job_application_id
        for m in messages
        if m.related_job_application_id is not None
    }
    summary_by_job = _thread_summary_map(db, user_id, job_ids)
    for message in messages:
        message.thread_summary = summary_by_job.get(
            message.related_job_application_id, dict(EMPTY_SUMMARY)
        )
    return messages
