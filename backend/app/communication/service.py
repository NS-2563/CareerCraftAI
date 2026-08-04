from sqlalchemy.orm import Session
from typing import Optional, List

from app.communication.models import CommunicationMessage
from app.communication.schemas import CommunicationMessageCreate, CommunicationMessageUpdate
from app.communication.conversation_status import (
    build_status_response,
    get_last_message,
    resolve_status,
    _last_message_map,
)
from app.models.job_application import JobApplication
from app.schemas.job_tracker import JobStatus
from app.utils.exceptions import NotFoundException
from app.utils.json_utils import to_json, from_json
from app.utils.versioned import create_version_snapshot, get_version_history, record_version, find_version
from app.activity.service import ActivityService
from app.activity.constants import EventType


def _get_all_fields_json(message: CommunicationMessage) -> dict:
    return {
        "message_type": message.message_type,
        "tone": message.tone,
        "direction": message.direction,
        "sender_name": message.sender_name,
        "sender_email": message.sender_email,
        "recipient_name": message.recipient_name,
        "recipient_role": message.recipient_role,
        "recipient_company": message.recipient_company,
        "subject": message.subject,
        "body": message.body,
    }


class CommunicationService:

    @staticmethod
    def create_from_generation(
        db: Session,
        user_id: int,
        message_type: str,
        tone: str,
        recipient_name: Optional[str],
        recipient_role: Optional[str],
        recipient_company: Optional[str],
        subject: str,
        body: str,
        related_job_application_id: Optional[int] = None,
        related_resume_id: Optional[int] = None,
        direction: str = "outbound",
        sender_name: Optional[str] = None,
        sender_email: Optional[str] = None,
    ) -> CommunicationMessage:
        message = CommunicationMessage(
            user_id=user_id,
            message_type=message_type,
            tone=tone,
            direction=direction,
            generation_method="ai_generated",
            sender_name=sender_name,
            sender_email=sender_email,
            recipient_name=recipient_name,
            recipient_role=recipient_role,
            recipient_company=recipient_company,
            subject=subject,
            body=body,
            related_job_application_id=related_job_application_id,
            related_resume_id=related_resume_id,
            version=1,
            version_history="[]",
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        ActivityService.log_event(
            db, user_id, EventType.COMMUNICATION_MESSAGE_GENERATED,
            title="Communication message generated",
            description=f"{message_type}: {subject[:80]}",
            related_entity_type="communication",
            related_entity_id=message.id,
            related_job_application_id=related_job_application_id,
        )
        return message

    @staticmethod
    def create(db: Session, user_id: int, data: CommunicationMessageCreate) -> CommunicationMessage:
        message = CommunicationMessage(
            user_id=user_id,
            message_type=data.message_type,
            tone=data.tone or "professional",
            direction=data.direction or "outbound",
            generation_method="manual",
            sender_name=data.sender_name,
            sender_email=data.sender_email,
            recipient_name=data.recipient_name,
            recipient_role=data.recipient_role,
            recipient_company=data.recipient_company,
            subject=data.subject,
            body=data.body,
            related_job_application_id=data.related_job_application_id,
            related_resume_id=data.related_resume_id,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        ActivityService.log_event(
            db, user_id, EventType.COMMUNICATION_MESSAGE_CREATED,
            title="Communication message created",
            description=f"{data.message_type}: {(data.subject or data.body or '')[:80]}",
            related_entity_type="communication",
            related_entity_id=message.id,
            related_job_application_id=data.related_job_application_id,
        )
        return message

    @staticmethod
    def log_inbound(
        db: Session,
        user_id: int,
        related_job_application_id: int,
        body: str,
        sender_name: Optional[str] = None,
        sender_email: Optional[str] = None,
        subject: Optional[str] = None,
        received_at=None,
    ) -> CommunicationMessage:
        """Persist a manually pasted inbound recruiter email against an application.

        The caller is responsible for ownership-checking the job application.
        """
        from datetime import datetime, timezone
        message = CommunicationMessage(
            user_id=user_id,
            message_type="recruiter_email",
            tone="professional",
            direction="inbound",
            generation_method="manual",
            sender_name=sender_name,
            sender_email=sender_email,
            recipient_name=None,
            recipient_role=None,
            recipient_company=None,
            subject=subject,
            body=body,
            related_job_application_id=related_job_application_id,
            related_resume_id=None,
            version=1,
            version_history="[]",
        )
        if received_at is not None:
            message.created_at = received_at
        db.add(message)
        db.commit()
        db.refresh(message)
        ActivityService.log_event(
            db, user_id, EventType.COMMUNICATION_MESSAGE_RECEIVED,
            title="Recruiter email logged",
            description=f"inbound: {subject or (body[:80])}",
            related_entity_type="communication",
            related_entity_id=message.id,
            related_job_application_id=related_job_application_id,
        )
        return message

    @staticmethod
    def get_thread(
        db: Session,
        user_id: int,
        job_application_id: int,
        limit: Optional[int] = None,
    ) -> List[CommunicationMessage]:
        """Return all messages (both directions) for a job application.

        Ownership-scoped to the given user. Ordered chronologically (created_at
        asc, id asc as a stable tiebreaker).
        """
        query = db.query(CommunicationMessage).filter(
            CommunicationMessage.user_id == user_id,
            CommunicationMessage.related_job_application_id == job_application_id,
        )
        query = query.order_by(
            CommunicationMessage.created_at.asc(),
            CommunicationMessage.id.asc(),
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_recent_thread(
        db: Session,
        user_id: int,
        job_application_id: int,
        n: int = 5,
    ) -> List[CommunicationMessage]:
        """Return the last ``n`` messages (chronological order) for an application.

        Used to give recruiter-reply generation full thread context. Excludes the
        single inbound message being replied to is NOT excluded here — callers pass
        the full recent history; the prompt delimiter marks all of it as data.
        """
        query = db.query(CommunicationMessage).filter(
            CommunicationMessage.user_id == user_id,
            CommunicationMessage.related_job_application_id == job_application_id,
        )
        recent_desc = query.order_by(
            CommunicationMessage.created_at.desc(),
            CommunicationMessage.id.desc(),
        ).limit(n).all()
        return list(reversed(recent_desc))

    @staticmethod
    def get_all(
        db: Session,
        user_id: int,
        message_type: Optional[str] = None,
        archived: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CommunicationMessage]:
        query = db.query(CommunicationMessage).filter(
            CommunicationMessage.user_id == user_id,
            CommunicationMessage.is_archived == archived,
        )
        if message_type:
            query = query.filter(CommunicationMessage.message_type == message_type)
        return query.order_by(CommunicationMessage.updated_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def _get_owned_job(db: Session, user_id: int, job_application_id: int) -> JobApplication:
        job = db.query(JobApplication).filter(
            JobApplication.id == job_application_id,
            JobApplication.user_id == user_id,
        ).first()
        if not job:
            raise NotFoundException("JobApplication", str(job_application_id))
        return job

    @staticmethod
    def get_conversation_status(
        db: Session, user_id: int, job_application_id: int
    ) -> dict:
        """Resolve the effective conversation status for one application."""
        job = CommunicationService._get_owned_job(db, user_id, job_application_id)
        last = get_last_message(db, user_id, job_application_id)
        return build_status_response(job, last)

    @staticmethod
    def set_conversation_status(
        db: Session,
        user_id: int,
        job_application_id: int,
        status: Optional[str],
    ) -> dict:
        """Set (or clear, when ``status`` is None) the manual override.

        The override only *surfaces* while the application is not in a terminal
        pipeline state — a terminal status always resolves to closed. The stored
        override is preserved so it is restored if the app is re-opened.
        """
        job = CommunicationService._get_owned_job(db, user_id, job_application_id)
        job.conversation_status_override = status if status in (
            "needs_reply", "waiting", "closed"
        ) else None
        db.commit()
        db.refresh(job)
        last = get_last_message(db, user_id, job_application_id)
        return build_status_response(job, last)

    @staticmethod
    def get_all_conversation_statuses(db: Session, user_id: int) -> list:
        """Resolve every application's conversation status (cross-app view)."""
        jobs = db.query(JobApplication).filter(
            JobApplication.user_id == user_id
        ).all()
        last_by_job = _last_message_map(
            db, user_id, [job.id for job in jobs]
        )
        results = []
        for job in jobs:
            status, source = resolve_status(job, last_by_job.get(job.id))
            results.append({
                "job_application_id": job.id,
                "company": job.company,
                "job_title": job.job_title,
                "application_status": (
                    job.status.value if isinstance(job.status, JobStatus) else str(job.status)
                ),
                "status": status,
                "source": source,
            })
        return results

    @staticmethod
    def attach_conversation_status(
        db: Session, messages: List[CommunicationMessage]
    ) -> List[CommunicationMessage]:
        """Attach transient conversation_status/source to each message.

        Reads the linked application's resolved status in one query and sets
        ``message.conversation_status`` / ``message.conversation_status_source``
        as plain Python attributes so the response schema can serialize them.
        """
        if not messages:
            return messages
        user_id = messages[0].user_id
        job_ids = {
            m.related_job_application_id
            for m in messages
            if m.related_job_application_id is not None
        }
        jobs = {}
        if job_ids:
            jobs = {
                job.id: job
                for job in db.query(JobApplication).filter(
                    JobApplication.id.in_(job_ids)
                ).all()
            }
        last_by_job = _last_message_map(db, user_id, job_ids)
        for message in messages:
            job = jobs.get(message.related_job_application_id)
            if job is None:
                message.conversation_status = None
                message.conversation_status_source = None
                continue
            status, source = resolve_status(job, last_by_job.get(job.id))
            message.conversation_status = status
            message.conversation_status_source = source
        return messages

    @staticmethod
    def get_by_id(db: Session, message_id: int, user_id: int) -> CommunicationMessage:
        message = db.query(CommunicationMessage).filter(
            CommunicationMessage.id == message_id,
            CommunicationMessage.user_id == user_id,
        ).first()
        if not message:
            raise NotFoundException("CommunicationMessage", str(message_id))
        return message

    @staticmethod
    def update(
        db: Session, message_id: int, user_id: int, update_data: CommunicationMessageUpdate
    ) -> CommunicationMessage:
        message = CommunicationService.get_by_id(db, message_id, user_id)

        snapshot = create_version_snapshot(message, _get_all_fields_json(message), "Before update")
        record_version(message, snapshot)

        data = update_data.model_dump(exclude_unset=True)

        if "message_type" in data and data["message_type"]:
            message.message_type = data["message_type"]
        if "tone" in data and data["tone"]:
            message.tone = data["tone"]
        if "direction" in data and data["direction"]:
            message.direction = data["direction"]
        if "sender_name" in data:
            message.sender_name = data["sender_name"]
        if "sender_email" in data:
            message.sender_email = data["sender_email"]
        if "recipient_name" in data:
            message.recipient_name = data["recipient_name"]
        if "recipient_role" in data:
            message.recipient_role = data["recipient_role"]
        if "recipient_company" in data:
            message.recipient_company = data["recipient_company"]
        if "subject" in data:
            message.subject = data["subject"]
        if "body" in data and data["body"] is not None:
            message.body = data["body"]
        if "related_job_application_id" in data:
            message.related_job_application_id = data["related_job_application_id"]
        if "related_resume_id" in data:
            message.related_resume_id = data["related_resume_id"]

        message.version += 1

        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def delete(db: Session, message_id: int, user_id: int) -> None:
        message = CommunicationService.get_by_id(db, message_id, user_id)
        db.delete(message)
        db.commit()

    @staticmethod
    def duplicate(db: Session, message_id: int, user_id: int, new_title: str) -> CommunicationMessage:
        original = CommunicationService.get_by_id(db, message_id, user_id)

        new_message = CommunicationMessage(
            user_id=user_id,
            message_type=original.message_type,
            tone=original.tone,
            direction=original.direction,
            generation_method=original.generation_method,
            sender_name=original.sender_name,
            sender_email=original.sender_email,
            recipient_name=original.recipient_name,
            recipient_role=original.recipient_role,
            recipient_company=original.recipient_company,
            subject=original.subject,
            body=original.body,
            related_job_application_id=original.related_job_application_id,
            related_resume_id=original.related_resume_id,
            version=1,
            version_history="[]",
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return new_message

    @staticmethod
    def rename(db: Session, message_id: int, user_id: int, new_subject: str) -> CommunicationMessage:
        message = CommunicationService.get_by_id(db, message_id, user_id)
        message.subject = new_subject
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def archive(db: Session, message_id: int, user_id: int) -> CommunicationMessage:
        message = CommunicationService.get_by_id(db, message_id, user_id)
        message.is_archived = True
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def restore(db: Session, message_id: int, user_id: int) -> CommunicationMessage:
        message = CommunicationService.get_by_id(db, message_id, user_id)
        message.is_archived = False
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_version_history(db: Session, message_id: int, user_id: int) -> List[dict]:
        message = CommunicationService.get_by_id(db, message_id, user_id)
        return get_version_history(message.version_history)

    @staticmethod
    def restore_version(db: Session, message_id: int, user_id: int, version: int) -> CommunicationMessage:
        message = CommunicationService.get_by_id(db, message_id, user_id)
        history = get_version_history(message.version_history)

        target = find_version(history, version)

        if not target:
            raise NotFoundException(f"Version {version}", "not found")

        data = target.get("data", {})

        snapshot = create_version_snapshot(message, _get_all_fields_json(message), f"Before restore to v{version}")
        record_version(message, snapshot)

        if "message_type" in data:
            message.message_type = data["message_type"]
        if "tone" in data:
            message.tone = data["tone"]
        if "direction" in data:
            message.direction = data["direction"]
        if "sender_name" in data:
            message.sender_name = data["sender_name"]
        if "sender_email" in data:
            message.sender_email = data["sender_email"]
        if "recipient_name" in data:
            message.recipient_name = data["recipient_name"]
        if "recipient_role" in data:
            message.recipient_role = data["recipient_role"]
        if "recipient_company" in data:
            message.recipient_company = data["recipient_company"]
        if "subject" in data:
            message.subject = data["subject"]
        if "body" in data:
            message.body = data["body"]

        message.version += 1

        db.commit()
        db.refresh(message)
        return message
