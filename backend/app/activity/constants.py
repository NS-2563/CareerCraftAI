from enum import Enum


class EventType(str, Enum):
    RESUME_CREATED = "resume_created"
    RESUME_UPDATED = "resume_updated"
    RESUME_ANALYZED = "resume_analyzed"
    RESUME_IMPORTED = "resume_imported"
    RESUME_DELETED = "resume_deleted"
    RESUME_DUPLICATED = "resume_duplicated"

    COVER_LETTER_CREATED = "cover_letter_created"
    COVER_LETTER_GENERATED = "cover_letter_generated"
    COVER_LETTER_UPDATED = "cover_letter_updated"
    COVER_LETTER_DELETED = "cover_letter_deleted"
    COVER_LETTER_DUPLICATED = "cover_letter_duplicated"

    JOB_APPLICATION_CREATED = "job_application_created"
    JOB_APPLICATION_STATUS_CHANGED = "job_application_status_changed"
    JOB_APPLICATION_UPDATED = "job_application_updated"
    JOB_APPLICATION_DELETED = "job_application_deleted"

    JOB_DESCRIPTION_ADDED = "job_description_added"
    JOB_DESCRIPTION_UPDATED = "job_description_updated"

    COMMUNICATION_MESSAGE_GENERATED = "communication_message_generated"
    COMMUNICATION_MESSAGE_CREATED = "communication_message_created"
    COMMUNICATION_MESSAGE_RECEIVED = "communication_message_received"
    COMMUNICATION_MESSAGE_UPDATED = "communication_message_updated"

    INTERVIEW_SESSION_COMPLETED = "interview_session_completed"
    INTERVIEW_SESSION_CREATED = "interview_session_created"
    INTERVIEW_QUESTIONS_GENERATED = "interview_questions_generated"

    CAREER_REPORT_GENERATED = "career_report_generated"
    CAREER_REPORT_SAVED = "career_report_saved"
    CAREER_REPORT_DELETED = "career_report_deleted"

    ANALYSIS_COMPLETED = "analysis_completed"
    JD_MATCH_ANALYZED = "jd_match_analyzed"


EVENT_TYPE_CHOICES = sorted([e.value for e in EventType])
