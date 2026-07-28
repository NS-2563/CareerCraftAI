from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List
import json

from app.communication.models import CommunicationMessage
from app.communication.schemas import CommunicationMessageCreate, CommunicationMessageUpdate
from app.utils.exceptions import NotFoundException


def _to_json(data) -> str:
    if data is None:
        return "[]"
    try:
        return json.dumps(data)
    except Exception:
        return "[]"


def _from_json(text: str) -> dict:
    if text:
        try:
            return json.loads(text)
        except Exception:
            pass
    return {}


def _create_version_snapshot(message: CommunicationMessage, note: str = None) -> dict:
    return {
        "version": message.version,
        "timestamp": datetime.utcnow().isoformat(),
        "note": note,
        "data": {
            "message_type": message.message_type,
            "tone": message.tone,
            "recipient_name": message.recipient_name,
            "recipient_role": message.recipient_role,
            "recipient_company": message.recipient_company,
            "subject": message.subject,
            "body": message.body,
        },
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
    ) -> CommunicationMessage:
        message = CommunicationMessage(
            user_id=user_id,
            message_type=message_type,
            tone=tone,
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
        return message

    @staticmethod
    def create(db: Session, user_id: int, data: CommunicationMessageCreate) -> CommunicationMessage:
        message = CommunicationMessage(
            user_id=user_id,
            message_type=data.message_type,
            tone=data.tone or "professional",
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
        return message

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

        snapshot = _create_version_snapshot(message, "Before update")
        history = _from_json(message.version_history) if message.version_history else []
        history.append(snapshot)
        message.version_history = _to_json(history[-50:])

        data = update_data.model_dump(exclude_unset=True)

        if "message_type" in data and data["message_type"]:
            message.message_type = data["message_type"]
        if "tone" in data and data["tone"]:
            message.tone = data["tone"]
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
        return _from_json(message.version_history) if message.version_history else []

    @staticmethod
    def restore_version(db: Session, message_id: int, user_id: int, version: int) -> CommunicationMessage:
        message = CommunicationService.get_by_id(db, message_id, user_id)
        history = _from_json(message.version_history) if message.version_history else []

        target = None
        for v in history:
            if v.get("version") == version:
                target = v
                break

        if not target:
            raise NotFoundException(f"Version {version}", "not found")

        data = target.get("data", {})

        snapshot = _create_version_snapshot(message, f"Before restore to v{version}")
        history.append(snapshot)
        message.version_history = _to_json(history[-50:])

        if "message_type" in data:
            message.message_type = data["message_type"]
        if "tone" in data:
            message.tone = data["tone"]
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
