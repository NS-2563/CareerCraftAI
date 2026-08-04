import logging
from datetime import datetime, timedelta

from sqlalchemy import func, nullslast, or_
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.job_application import JobApplication
from app.models.career_report import CareerReport
from app.models.cover_letter import CoverLetter
from app.communication.models import CommunicationMessage
from app.interview_prep.models import InterviewSession
from app.activity.service import ActivityService
from app.analytics.service import AnalyticsService
from app.communication.suggestions_service import get_active_suggestions
from app.career.services.analytics_service import get_skill_gap_summary
from app.schemas.job_tracker import JobStatus
from app.dashboard.focus_service import get_today_focus, get_today_focus_items

logger = logging.getLogger(__name__)


def _practice_interview_filter():
    """Match practice interview sessions only (excludes real-interview logs).

    Real-interview logs are a distinct, application-linked entry type; they
    must not inflate practice session counts or averages.
    """
    from app.interview_prep.service import SESSION_TYPE_PRACTICE

    return or_(
        InterviewSession.session_type == SESSION_TYPE_PRACTICE,
        InterviewSession.session_type.is_(None),
    )


class DashboardService:

    @staticmethod
    def get_summary(db: Session, user_id: int) -> dict:
        summary = {}

        # --- Resume ---
        try:
            resume_count = (
                db.query(func.count(Resume.id))
                .filter(Resume.user_id == user_id, Resume.is_archived == False)
                .scalar()
                or 0
            )

            last_resume = (
                db.query(Resume)
                .filter(Resume.user_id == user_id, Resume.is_archived == False)
                .order_by(nullslast(Resume.updated_at.desc()), Resume.created_at.desc())
                .first()
            )

            has_completed = (
                db.query(func.count(Resume.id))
                .filter(
                    Resume.user_id == user_id,
                    Resume.is_archived == False,
                    Resume.completed == True,
                )
                .scalar()
                or 0
            ) > 0

            created_this_week = (
                db.query(func.count(Resume.id))
                .filter(
                    Resume.user_id == user_id,
                    Resume.is_archived == False,
                    Resume.created_at >= datetime.utcnow() - timedelta(days=7),
                )
                .scalar()
                or 0
            )

            summary["resume"] = {
                "count": resume_count,
                "last_edited": (
                    last_resume.updated_at.isoformat()
                    if last_resume and last_resume.updated_at
                    else (
                        last_resume.created_at.isoformat()
                        if last_resume
                        else None
                    )
                ),
                "last_name": last_resume.name if last_resume else None,
                "last_id": last_resume.id if last_resume else None,
                "has_completed": has_completed,
                "created_this_week": created_this_week,
            }
        except Exception:
            logger.warning("Dashboard resume section failed", exc_info=True)
            summary["resume"] = None

        # --- Job Stats ---
        try:
            total_apps = (
                db.query(func.count(JobApplication.id))
                .filter(JobApplication.user_id == user_id)
                .scalar()
                or 0
            )
            interview_count = (
                db.query(func.count(JobApplication.id))
                .filter(
                    JobApplication.user_id == user_id,
                    JobApplication.status == JobStatus.INTERVIEW,
                )
                .scalar()
                or 0
            )

            last_job = (
                db.query(JobApplication)
                .filter(JobApplication.user_id == user_id)
                .order_by(nullslast(JobApplication.updated_at.desc()), JobApplication.created_at.desc())
                .first()
            )

            summary["job_stats"] = {
                "total_applications": total_apps,
                "interview_count": interview_count,
            }

            # Stage-by-stage pipeline counts (real Job Tracker statuses).
            stage_counts = dict(
                (
                    db.query(JobApplication.status, func.count(JobApplication.id))
                    .filter(JobApplication.user_id == user_id)
                    .group_by(JobApplication.status)
                    .all()
                )
            )
            pipeline_order = [
                JobStatus.WISHLIST,
                JobStatus.APPLIED,
                JobStatus.INTERVIEW,
                JobStatus.OFFER,
            ]
            summary["job_pipeline"] = [
                {
                    "status": s.value,
                    "count": stage_counts.get(s, 0),
                    "pct": round(stage_counts.get(s, 0) / total_apps * 100) if total_apps else 0,
                }
                for s in pipeline_order
            ]

            summary["last_job"] = (
                {
                    "id": last_job.id,
                    "company": last_job.company,
                    "job_title": last_job.job_title,
                    "status": last_job.status,
                }
                if last_job
                else None
            )
        except Exception:
            logger.warning("Dashboard job_stats section failed", exc_info=True)
            summary["job_stats"] = None
            summary["last_job"] = None

        # --- Interview ---
        try:
            total_sessions = (
                db.query(func.count(InterviewSession.id))
                .filter(
                    InterviewSession.user_id == user_id,
                    _practice_interview_filter(),
                )
                .scalar()
                or 0
            )

            completed_sessions = (
                db.query(InterviewSession)
                .filter(
                    InterviewSession.user_id == user_id,
                    _practice_interview_filter(),
                    InterviewSession.overall_score != None,
                )
                .all()
            )
            avg_score = (
                round(
                    sum(s.overall_score for s in completed_sessions)
                    / len(completed_sessions),
                    1,
                )
                if completed_sessions
                else None
            )

            latest_session = (
                db.query(InterviewSession)
                .filter(
                    InterviewSession.user_id == user_id,
                    _practice_interview_filter(),
                )
                .order_by(InterviewSession.created_at.desc())
                .first()
            )

            latest_incomplete = (
                db.query(InterviewSession)
                .filter(
                    InterviewSession.user_id == user_id,
                    _practice_interview_filter(),
                    InterviewSession.completed_at == None,
                )
                .order_by(InterviewSession.created_at.desc())
                .first()
            )

            summary["interview"] = {
                "total_sessions": total_sessions,
                "average_score": avg_score,
                "latest_session": (
                    {
                        "id": latest_session.id,
                        "job_title": latest_session.job_title,
                        "completed": latest_session.completed_at is not None,
                        "score": latest_session.overall_score,
                    }
                    if latest_session
                    else None
                ),
                "latest_incomplete_session": (
                    {
                        "id": latest_incomplete.id,
                        "job_title": latest_incomplete.job_title,
                    }
                    if latest_incomplete
                    else None
                ),
            }
        except Exception:
            logger.warning("Dashboard interview section failed", exc_info=True)
            summary["interview"] = None

        # --- Career Readiness ---
        try:
            latest_report = (
                db.query(CareerReport)
                .filter(CareerReport.user_id == user_id)
                .order_by(CareerReport.created_at.desc())
                .first()
            )
            summary["career_readiness"] = (
                {
                    "score": latest_report.readiness_score,
                    "last_updated": (
                        latest_report.created_at.isoformat()
                        if latest_report.created_at
                        else None
                    ),
                }
                if latest_report
                else None
            )
        except Exception:
            logger.warning("Dashboard career_readiness section failed", exc_info=True)
            summary["career_readiness"] = None

        # --- Today's Focus ---
        try:
            summary["today_focus"] = get_today_focus(db, user_id)
            summary["focus_items"] = get_today_focus_items(db, user_id, limit=3)
        except Exception:
            logger.warning("Dashboard today_focus section failed", exc_info=True)
            summary["today_focus"] = None
            summary["focus_items"] = []

        # --- Recent Activity ---
        try:
            activity = ActivityService.get_recent(db, user_id, limit=10)
            summary["recent_activity"] = [
                {
                    "id": a.id,
                    "event_type": a.event_type,
                    "title": a.title,
                    "description": a.description,
                    "related_entity_type": a.related_entity_type,
                    "related_entity_id": a.related_entity_id,
                    "related_job_application_id": a.related_job_application_id,
                    "created_at": (
                        a.created_at.isoformat() if a.created_at else None
                    ),
                }
                for a in activity
            ]
        except Exception:
            logger.warning("Dashboard recent_activity section failed", exc_info=True)
            summary["recent_activity"] = []

        # --- Continue Where You Left Off ---
        try:
            continue_items = {}

            last_resume = (
                db.query(Resume)
                .filter(Resume.user_id == user_id, Resume.is_archived == False)
                .order_by(nullslast(Resume.updated_at.desc()), Resume.created_at.desc())
                .first()
            )
            if last_resume:
                continue_items["resume"] = {
                    "id": last_resume.id,
                    "label": last_resume.name,
                    "type": "resume",
                    "path": "/resume-studio",
                }

            last_cl = (
                db.query(CoverLetter)
                .filter(
                    CoverLetter.user_id == user_id,
                    CoverLetter.is_archived == False,
                )
                .order_by(nullslast(CoverLetter.updated_at.desc()), CoverLetter.created_at.desc())
                .first()
            )
            if last_cl:
                continue_items["cover_letter"] = {
                    "id": last_cl.id,
                    "label": last_cl.title or last_cl.job_title or "Cover Letter",
                    "type": "cover_letter",
                    "path": "/cover-letter-studio",
                }

            last_msg = (
                db.query(CommunicationMessage)
                .filter(
                    CommunicationMessage.user_id == user_id,
                    CommunicationMessage.is_archived == False,
                )
                .order_by(nullslast(CommunicationMessage.updated_at.desc()), CommunicationMessage.created_at.desc())
                .first()
            )
            if last_msg:
                continue_items["communication"] = {
                    "id": last_msg.id,
                    "label": last_msg.subject or last_msg.recipient_name or "Message",
                    "type": "communication",
                    "path": "/communication",
                }

            last_session = (
                db.query(InterviewSession)
                .filter(
                    InterviewSession.user_id == user_id,
                    _practice_interview_filter(),
                )
                .order_by(InterviewSession.created_at.desc())
                .first()
            )
            if last_session:
                continue_items["interview"] = {
                    "id": last_session.id,
                    "label": last_session.job_title or "Interview Practice",
                    "type": "interview",
                    "path": "/interview/practice" if last_session.completed_at is None else "/interview/dashboard",
                }

            last_job = (
                db.query(JobApplication)
                .filter(JobApplication.user_id == user_id)
                .order_by(nullslast(JobApplication.updated_at.desc()), JobApplication.created_at.desc())
                .first()
            )
            if last_job:
                continue_items["job_application"] = {
                    "id": last_job.id,
                    "label": f"{last_job.job_title or 'Position'} at {last_job.company or 'Company'}",
                    "type": "job_application",
                    "path": "/jobs",
                }

            summary["continue_items"] = continue_items
        except Exception:
            logger.warning("Dashboard continue_items section failed", exc_info=True)
            summary["continue_items"] = {}

        # --- Career Journey ---
        try:
            has_resume = (
                db.query(func.count(Resume.id))
                .filter(
                    Resume.user_id == user_id,
                    Resume.is_archived == False,
                    Resume.completed == True,
                )
                .scalar()
                or 0
            ) > 0

            has_analysis = (
                db.query(func.count(ResumeAnalysis.id))
                .filter(ResumeAnalysis.user_id == user_id)
                .scalar()
                or 0
            ) > 0

            has_career_report = (
                db.query(func.count(CareerReport.id))
                .filter(CareerReport.user_id == user_id)
                .scalar()
                or 0
            ) > 0

            has_job_app = total_apps > 0 if summary.get("job_stats") else False

            has_interview = total_sessions > 0 if summary.get("interview") else False

            has_communication = (
                db.query(func.count(CommunicationMessage.id))
                .filter(
                    CommunicationMessage.user_id == user_id,
                    CommunicationMessage.is_archived == False,
                )
                .scalar()
                or 0
            ) > 0

            def journey_status(flag):
                return "complete" if flag else "not_started"

            summary["career_journey"] = [
                {
                    "id": "resume",
                    "label": "Build Resume",
                    "status": journey_status(has_resume),
                },
                {
                    "id": "analysis",
                    "label": "Resume Analysis",
                    "status": journey_status(has_analysis),
                },
                {
                    "id": "career_coach",
                    "label": "Career Coach",
                    "status": journey_status(has_career_report),
                },
                {
                    "id": "job_applications",
                    "label": "Job Applications",
                    "status": journey_status(has_job_app),
                },
                {
                    "id": "interview_prep",
                    "label": "Interview Prep",
                    "status": journey_status(has_interview),
                },
                {
                    "id": "communication",
                    "label": "Communication",
                    "status": journey_status(has_communication),
                },
            ]
        except Exception:
            logger.warning("Dashboard career_journey section failed", exc_info=True)
            summary["career_journey"] = []

        # --- AI Insights ---
        try:
            insights = []

            pending_suggestions = get_active_suggestions(db, user_id)
            summary["pending_follow_ups"] = sum(
                1
                for s in pending_suggestions
                if s.get("suggestion_type") == "follow_up_due"
                and not s.get("is_actioned")
            )
            for s in pending_suggestions[:3]:
                insights.append({
                    "type": "follow_up",
                    "message": f"Follow up with {s.get('job_company', 'a company')} regarding {s.get('job_title', 'the position')}",
                    "priority": "medium",
                })

            if summary.get("interview") and summary["interview"]["total_sessions"] > 0:
                last_interview_activity = None
                for act in activity if activity else []:
                    if act.event_type.startswith("interview"):
                        last_interview_activity = act.created_at
                        break
                if last_interview_activity:
                    if isinstance(last_interview_activity, str):
                        last_interview_activity = last_interview_activity.replace("Z", "+00:00")
                    last_time = last_interview_activity if isinstance(last_interview_activity, datetime) else datetime.fromisoformat(last_interview_activity)
                    days_since = (datetime.utcnow() - last_time).days
                    if days_since >= 7:
                        insights.append({
                            "type": "practice_reminder",
                            "message": f"You haven't practiced interview questions in {days_since} days",
                            "priority": "low",
                        })

            if summary.get("career_readiness"):
                score = summary["career_readiness"]["score"]
                insights.append({
                    "type": "readiness_score",
                    "message": f"Your career readiness score is {score}/100",
                    "priority": "info",
                })

            ats_snapshots = AnalyticsService.get_history(
                db, user_id, "ats_score", limit=2
            )
            if len(ats_snapshots) >= 2:
                latest_val = ats_snapshots[-1].value
                prev_val = ats_snapshots[-2].value
                if prev_val > 0:
                    pct_change = round((latest_val - prev_val) / prev_val * 100, 1)
                    direction = "improved" if pct_change > 0 else "declined"
                    insights.append({
                        "type": "ats_trend",
                        "message": f"ATS score {direction} by {abs(pct_change)}%",
                        "priority": "info",
                    })

            skill_gap = get_skill_gap_summary(db, user_id)
            if skill_gap.get("has_data") and skill_gap["top_missing_skills"]:
                total = skill_gap["total_applications"]
                top = skill_gap["top_missing_skills"][0]
                insights.append({
                    "type": "skill_gap",
                    "message": (
                        f"{top['name']} is missing from your resume and required "
                        f"in {top['count']} of your last {total} applications"
                    ),
                    "priority": "high",
                })

            summary["ai_insights"] = insights
        except Exception:
            logger.warning("Dashboard ai_insights section failed", exc_info=True)
            summary["ai_insights"] = []
            summary.setdefault("pending_follow_ups", 0)

        # --- Empty state detection ---
        resume_count_val = (
            summary.get("resume", {}).get("count", 0) if summary.get("resume") else 0
        )
        activity_count = len(summary.get("recent_activity", []))
        summary["is_empty"] = resume_count_val == 0 and activity_count == 0

        return summary
