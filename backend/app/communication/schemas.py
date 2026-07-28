from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional, List

_MESSAGE_TYPE_PATTERN = r"^(cold_email|follow_up|thank_you|linkedin_note|referral_request|recruiter_reply)$"
_REPLY_INTENTS = {"accept_interest", "decline_politely", "negotiate_timing", "ask_clarifying_questions"}


class CommunicationMessageBase(BaseModel):
    message_type: str = Field(..., pattern=_MESSAGE_TYPE_PATTERN)
    tone: str = Field(default="professional")
    recipient_name: Optional[str] = Field(default=None, max_length=255)
    recipient_role: Optional[str] = Field(default=None, max_length=255)
    recipient_company: Optional[str] = Field(default=None, max_length=255)
    subject: Optional[str] = Field(default=None, max_length=500)
    body: Optional[str] = None
    related_job_application_id: Optional[int] = None
    related_resume_id: Optional[int] = None


class CommunicationMessageCreate(CommunicationMessageBase):
    body: str = Field(..., min_length=1)


class CommunicationMessageUpdate(BaseModel):
    message_type: Optional[str] = Field(default=None, pattern=_MESSAGE_TYPE_PATTERN)
    tone: Optional[str] = None
    recipient_name: Optional[str] = Field(default=None, max_length=255)
    recipient_role: Optional[str] = Field(default=None, max_length=255)
    recipient_company: Optional[str] = Field(default=None, max_length=255)
    subject: Optional[str] = Field(default=None, max_length=500)
    body: Optional[str] = None
    related_job_application_id: Optional[int] = None
    related_resume_id: Optional[int] = None


class CommunicationMessageResponse(BaseModel):
    id: int
    user_id: int
    message_type: str
    tone: str = "professional"
    recipient_name: Optional[str] = None
    recipient_role: Optional[str] = None
    recipient_company: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    related_job_application_id: Optional[int] = None
    related_resume_id: Optional[int] = None
    version: int = 1
    is_archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GenerateMessageRequest(BaseModel):
    message_type: str = Field(..., pattern=_MESSAGE_TYPE_PATTERN)
    tone: str = Field(default="professional")
    recipient_name: Optional[str] = Field(default=None, max_length=255)
    recipient_role: Optional[str] = Field(default=None, max_length=255)
    recipient_company: Optional[str] = Field(default=None, max_length=255)
    custom_context: Optional[str] = Field(default=None, max_length=2000)
    related_job_application_id: Optional[int] = None
    related_resume_id: Optional[int] = None
    inbound_message: Optional[str] = Field(default=None, max_length=10000)
    reply_intent: Optional[str] = None

    @model_validator(mode="after")
    def validate_recruiter_reply(self):
        if self.message_type == "recruiter_reply":
            if not self.inbound_message or not self.inbound_message.strip():
                raise ValueError("inbound_message is required when message_type is 'recruiter_reply'")
            if self.reply_intent not in _REPLY_INTENTS:
                raise ValueError(f"reply_intent must be one of: {', '.join(sorted(_REPLY_INTENTS))}")
        return self


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class DuplicateRequest(BaseModel):
    title: str = Field(default="Copy of Message")


class VersionRestoreRequest(BaseModel):
    version: int = Field(..., ge=1)
