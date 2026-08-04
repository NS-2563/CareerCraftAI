"""Milestone detection — first-occurrence achievements over real Activity Log data.

Every milestone is backed by a real logged ``ActivityEvent`` (first occurrence
of one of its event types). There is no new tracking system: this reads the same
Activity Log the rest of the app already writes. A milestone is achieved iff at
least one of its event types has been logged, and ``achieved_at`` is the earliest
such event's timestamp. No inference, no fabrication.
"""

from typing import List

from sqlalchemy.orm import Session

from app.activity.models import ActivityEvent

# Exact, defined milestone list. event_types: any ONE of these achieves it.
MILESTONES = [
    {
        "key": "first_resume",
        "label": "First resume created",
        "description": "Created or imported your first resume.",
        "event_types": ["resume_created", "resume_imported"],
    },
    {
        "key": "first_resume_analysis",
        "label": "First resume analyzed",
        "description": "Ran your first resume analysis.",
        "event_types": ["resume_analyzed", "analysis_completed"],
    },
    {
        "key": "first_application",
        "label": "First application logged",
        "description": "Logged your first job application.",
        "event_types": ["job_application_created"],
    },
    {
        "key": "first_jd_match",
        "label": "First JD match run",
        "description": "Matched a resume against a job description.",
        "event_types": ["jd_match_analyzed"],
    },
    {
        "key": "first_cover_letter",
        "label": "First cover letter generated",
        "description": "Generated or saved your first cover letter.",
        "event_types": ["cover_letter_generated", "cover_letter_created"],
    },
    {
        "key": "first_interview",
        "label": "First interview completed",
        "description": "Completed your first interview session.",
        "event_types": ["interview_session_completed"],
    },
    {
        "key": "first_message",
        "label": "First message sent",
        "description": "Created your first communication message.",
        "event_types": [
            "communication_message_generated",
            "communication_message_created",
        ],
    },
    {
        "key": "first_career_report",
        "label": "First career report",
        "description": "Generated your first career report.",
        "event_types": ["career_report_generated"],
    },
]


def detect_milestones(db: Session, user_id: int) -> List[dict]:
    """Return the milestone list with achieved/achieved_at derived from real
    Activity Log events (first occurrence per event type).

    One query, oldest-first; the earliest event of each type wins. Output order
    is the defined MILESTONES order — stable and deterministic.
    """
    events = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.user_id == user_id)
        .order_by(ActivityEvent.created_at.asc(), ActivityEvent.id.asc())
        .all()
    )

    first_by_type = {}
    for event in events:
        if event.event_type not in first_by_type:
            first_by_type[event.event_type] = event.created_at

    results = []
    for milestone in MILESTONES:
        timestamps = [
            first_by_type[t]
            for t in milestone["event_types"]
            if t in first_by_type
        ]
        achieved = bool(timestamps)
        achieved_at = (
            min(timestamps).isoformat() if timestamps else None
        )
        results.append({
            "key": milestone["key"],
            "label": milestone["label"],
            "description": milestone["description"],
            "achieved": achieved,
            "achieved_at": achieved_at,
        })

    return results