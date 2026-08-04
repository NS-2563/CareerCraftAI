from pydantic import BaseModel, Field, model_validator, field_validator
from datetime import datetime
from typing import Optional, List

_MESSAGE_TYPE_PATTERN = r"^(cold_email|follow_up|thank_you|linkedin_note|referral_request|recruiter_reply)$"
_REPLY_INTENTS = {"accept_interest", "decline_politely", "negotiate_timing", "ask_clarifying_questions"}
_DIRECTIONS = {"outbound", "inbound"}


class CommunicationMessageBase(BaseModel):
    message_type: str = Field(..., pattern=_MESSAGE_TYPE_PATTERN)
    tone: str = Field(default="professional")
    direction: str = Field(default="outbound", pattern=r"^(outbound|inbound)$")
    sender_name: Optional[str] = Field(default=None, max_length=255)
    sender_email: Optional[str] = Field(default=None, max_length=255)
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
    direction: Optional[str] = Field(default=None, pattern=r"^(outbound|inbound)$")
    sender_name: Optional[str] = Field(default=None, max_length=255)
    sender_email: Optional[str] = Field(default=None, max_length=255)
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
    direction: str = "outbound"
    generation_method: str = "manual"
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
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
    # Resolved conversation status of the linked application (transient,
    # attached by the service; None when no application is linked).
    conversation_status: Optional[str] = None
    conversation_status_source: Optional[str] = None
    # Deterministic per-application thread summary (transient, attached by the
    # service): last_reply / last_recruiter_email / response_overdue / state.
    thread_summary: Optional[dict] = None

    model_config = {"from_attributes": True}


_CONVERSATION_STATUS_PATTERN = r"^(needs_reply|waiting|closed)$"


class ConversationStatusUpdateRequest(BaseModel):
    """Set the explicit conversation-status override.

    ``status`` may be null to clear the override and return to automatic
    derivation from message direction + application status.
    """

    status: Optional[str] = Field(
        default=None,
        pattern=_CONVERSATION_STATUS_PATTERN,
        description="'needs_reply', 'waiting', 'closed', or null to clear.",
    )


class ConversationStatusResponse(BaseModel):
    """One application's resolved conversation status and why it is what it is."""

    job_application_id: int
    status: Optional[str] = None
    source: str
    application_status: str
    last_message_direction: Optional[str] = None


class ApplicationConversationStatus(BaseModel):
    """Cross-application conversation status row (Communication Hub view)."""

    job_application_id: int
    company: str
    job_title: str
    application_status: str
    status: Optional[str] = None
    source: str


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
    thread_context: Optional[bool] = Field(
        default=True,
        description="When True and related_job_application_id is set for a recruiter_reply, "
                    "include the application's recent thread as prompt context.",
    )

    @model_validator(mode="after")
    def validate_recruiter_reply(self):
        if self.message_type == "recruiter_reply":
            if not self.inbound_message or not self.inbound_message.strip():
                raise ValueError("inbound_message is required when message_type is 'recruiter_reply'")
            if self.reply_intent not in _REPLY_INTENTS:
                raise ValueError(f"reply_intent must be one of: {', '.join(sorted(_REPLY_INTENTS))}")
        return self


class LogInboundMessageRequest(BaseModel):
    """Log a recruiter's email manually against a specific job application.

    Inbound messages are pasted by the user for this phase — no Gmail/email
    provider integration is involved.
    """

    related_job_application_id: int = Field(..., description="The job application this email belongs to")
    sender_name: Optional[str] = Field(default=None, max_length=255)
    sender_email: Optional[str] = Field(default=None, max_length=255)
    subject: Optional[str] = Field(default=None, max_length=500)
    body: str = Field(..., min_length=1)
    received_at: Optional[datetime] = Field(
        default=None, description="When the email was received; defaults to now."
    )


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class DuplicateRequest(BaseModel):
    title: str = Field(default="Copy of Message")


class VersionRestoreRequest(BaseModel):
    version: int = Field(..., ge=1)
