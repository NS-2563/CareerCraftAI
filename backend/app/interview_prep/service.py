import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import func as sa_func
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.interview_prep.schemas import (
    GenerateQuestionsRequest,
    GeneratedQuestion,
    EvaluateAnswerRequest,
    AnswerEvaluation,
    EvaluateAnswerResponse,
    CreateSessionRequest,
    UpdateSessionRequest,
    CreateRealInterviewRequest,
    SessionListItem,
    SessionDetail,
    ProgressOverview,
    ProgressByRoleItem,
    ProgressByCategoryItem,
    ProgressResponse,
)
from app.interview_prep.models import InterviewSession
from app.models.job_application import JobApplication
from app.providers.factory import get_provider
from app.utils.exceptions import NotFoundException
from app.activity.service import ActivityService
from app.activity.constants import EventType
from app.analytics.service import AnalyticsService

logger = logging.getLogger(__name__)

SESSION_TYPE_PRACTICE = "practice"
SESSION_TYPE_REAL_INTERVIEW = "real_interview"


def normalize_job_role(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return None
    val = value.strip().lower()
    val = re.sub(r"\s+", " ", val)
    return val if val else None


class InterviewPrepService:

    @staticmethod
    def _lookup_job_context(
        db: Session,
        job_application_id: int,
        user_id: int,
    ) -> tuple:
        company = None
        job_title = None
        job_description = None

        job = db.query(JobApplication).filter(
            JobApplication.id == job_application_id,
            JobApplication.user_id == user_id,
        ).first()

        if not job:
            raise NotFoundException("JobApplication", str(job_application_id))

        company = job.company
        job_title = job.job_title
        job_description = job.job_description

        return company, job_title, job_description

    @staticmethod
    def generate_questions(
        db: Session,
        user_id: int,
        request: GenerateQuestionsRequest,
    ) -> List[GeneratedQuestion]:
        company = None
        resolved_job_title = request.job_title
        job_description = None

        if request.related_job_application_id is not None:
            company, resolved_job_title, job_description = (
                InterviewPrepService._lookup_job_context(
                    db, request.related_job_application_id, user_id,
                )
            )

        provider = get_provider()
        result = provider.generate_interview_questions(
            job_title=resolved_job_title,
            job_role=request.job_role,
            skills=request.skills,
            difficulty=request.difficulty,
            question_count=request.question_count,
            company=company,
            job_description=job_description,
        )

        ActivityService.log_event(
            db, user_id, EventType.INTERVIEW_QUESTIONS_GENERATED,
            title="Interview questions generated",
            description=resolved_job_title or request.job_role or "General practice",
            related_entity_type="interview_session",
            related_job_application_id=request.related_job_application_id,
        )

        return result.get("questions", [])

    @staticmethod
    def evaluate_answer(
        request: EvaluateAnswerRequest,
    ) -> EvaluateAnswerResponse:
        provider = get_provider()
        result = provider.generate_answer_evaluation(
            question=request.question,
            answer=request.answer,
            job_title=request.job_title,
            difficulty=request.difficulty,
        )

        if result.get("evaluation_failed"):
            return EvaluateAnswerResponse(
                evaluation=AnswerEvaluation(score=0, strengths=[], improvements=[]),
                evaluation_failed=True,
            )

        evaluation_data = result.get("evaluation", {})
        evaluation = AnswerEvaluation(
            score=evaluation_data.get("score", 0),
            strengths=evaluation_data.get("strengths", []),
            improvements=evaluation_data.get("improvements", []),
            model_answer_notes=evaluation_data.get("model_answer_notes"),
        )
        return EvaluateAnswerResponse(evaluation=evaluation, evaluation_failed=False)

    @staticmethod
    def create_session(
        db: Session,
        user_id: int,
        request: CreateSessionRequest,
    ) -> SessionDetail:
        session = InterviewSession(
            user_id=user_id,
            session_type=SESSION_TYPE_PRACTICE,
            related_job_application_id=request.related_job_application_id,
            job_title=request.job_title,
            job_role_normalized=normalize_job_role(request.job_title),
            skills=json.dumps(request.skills) if request.skills else None,
            difficulty=request.difficulty,
            question_count=request.question_count,
            questions=json.dumps([q.model_dump() for q in request.questions]) if request.questions else None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        ActivityService.log_event(
            db, user_id, EventType.INTERVIEW_SESSION_CREATED,
            title="Interview practice started",
            description=request.job_title or "General practice",
            related_entity_type="interview_session",
            related_entity_id=session.id,
            related_job_application_id=request.related_job_application_id,
        )
        return _session_to_detail(session)

    @staticmethod
    def create_real_interview(
        db: Session,
        user_id: int,
        request: CreateRealInterviewRequest,
    ) -> SessionDetail:
        """Record a retrospective real-interview log tied to a job application.

        The application must exist and belong to the user. The application's
        job title/company are captured onto the session so the log reads well
        even if the application is later deleted.
        """
        company, job_title, _ = InterviewPrepService._lookup_job_context(
            db, request.job_application_id, user_id,
        )

        session = InterviewSession(
            user_id=user_id,
            session_type=SESSION_TYPE_REAL_INTERVIEW,
            related_job_application_id=request.job_application_id,
            job_title=job_title,
            job_role_normalized=normalize_job_role(job_title),
            company_name=company,
            question_count=0,
            how_it_went=request.how_it_went,
            self_rated_confidence=request.self_rated_confidence,
            questions_asked=request.questions_asked,
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        ActivityService.log_event(
            db, user_id, EventType.INTERVIEW_SESSION_COMPLETED,
            title="Real interview logged",
            description=job_title or "Real interview",
            related_entity_type="interview_session",
            related_entity_id=session.id,
            related_job_application_id=request.job_application_id,
        )

        return _session_to_detail(session)

    @staticmethod
    def list_real_interviews_for_application(
        db: Session,
        user_id: int,
        job_application_id: int,
    ) -> List[SessionDetail]:
        """Return all real-interview logs for a user's job application."""
        InterviewPrepService._lookup_job_context(db, job_application_id, user_id)

        sessions = (
            db.query(InterviewSession)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewSession.session_type == SESSION_TYPE_REAL_INTERVIEW,
                InterviewSession.related_job_application_id == job_application_id,
            )
            .order_by(InterviewSession.created_at.desc(), InterviewSession.id.desc())
            .all()
        )
        return [_session_to_detail(s) for s in sessions]

    @staticmethod
    def list_sessions_for_application(
        db: Session,
        user_id: int,
        job_application_id: int,
    ) -> List[SessionDetail]:
        """Return ALL interview sessions (practice + real-interview logs) tied to
        a user's job application, oldest first.

        Used by the per-application timeline so interview events can be
        interleaved chronologically with communication messages.
        """
        InterviewPrepService._lookup_job_context(db, job_application_id, user_id)

        sessions = (
            db.query(InterviewSession)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewSession.related_job_application_id == job_application_id,
            )
            .order_by(InterviewSession.created_at.asc(), InterviewSession.id.asc())
            .all()
        )
        return [_session_to_detail(s) for s in sessions]

    @staticmethod
    def update_session(
        db: Session,
        user_id: int,
        session_id: int,
        request: UpdateSessionRequest,
    ) -> SessionDetail:
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        ).first()
        if not session:
            raise NotFoundException("InterviewSession", str(session_id))

        if request.answers is not None:
            session.answers = json.dumps(request.answers)

        if request.overall_score is not None:
            session.overall_score = request.overall_score

        if request.completed_at:
            try:
                session.completed_at = datetime.fromisoformat(request.completed_at)
            except (ValueError, TypeError):
                session.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db.commit()
        db.refresh(session)

        if request.overall_score is not None:
            ActivityService.log_event(
                db, user_id, EventType.INTERVIEW_SESSION_COMPLETED,
                title="Interview session completed",
                description=session.job_title or "General practice",
                related_entity_type="interview_session",
                related_entity_id=session.id,
                related_job_application_id=session.related_job_application_id,
            )
            AnalyticsService.record_snapshot(
                db, user_id, "interview_average", float(request.overall_score),
            )

        return _session_to_detail(session)

    @staticmethod
    def list_sessions(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        session_type: Optional[str] = None,
    ) -> tuple:
        query = db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id,
        )

        if session_type is not None:
            query = query.filter(InterviewSession.session_type == session_type)

        query = query.order_by(InterviewSession.created_at.desc(), InterviewSession.id.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size

        result = []
        for s in items:
            started_str = s.started_at.isoformat() if s.started_at else None
            completed_str = s.completed_at.isoformat() if s.completed_at else None
            created_str = s.created_at.isoformat() if s.created_at else None
            result.append(SessionListItem(
                id=s.id,
                session_type=s.session_type or SESSION_TYPE_PRACTICE,
                job_title=s.job_title,
                difficulty=s.difficulty,
                question_count=s.question_count,
                overall_score=s.overall_score,
                self_rated_confidence=s.self_rated_confidence,
                related_job_application_id=s.related_job_application_id,
                started_at=started_str,
                completed_at=completed_str,
                created_at=created_str,
            ))

        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
        return result, pagination

    @staticmethod
    def get_session(
        db: Session,
        user_id: int,
        session_id: int,
    ) -> SessionDetail:
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        ).first()
        if not session:
            raise NotFoundException("InterviewSession", str(session_id))
        return _session_to_detail(session)


    @staticmethod
    def get_progress(
        db: Session,
        user_id: int,
        sort: str = "score_asc",
    ) -> ProgressResponse:
        """Aggregate progress metrics for a user.

        All aggregation happens server-side — no raw session data sent to the frontend.
        """
        TREND_MIN_SESSIONS = 4
        TREND_RECENT_N = 5

        # Progress aggregates practice performance only — real-interview logs are
        # a distinct, separately-weighted signal and are excluded here.
        all_sessions = db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id,
            or_(
                InterviewSession.session_type == SESSION_TYPE_PRACTICE,
                InterviewSession.session_type.is_(None),
            ),
        ).order_by(InterviewSession.created_at.asc()).all()

        total_sessions = len(all_sessions)
        completed = [s for s in all_sessions if s.overall_score is not None]

        # --- overview ---
        avg_score = None
        trend = "not_enough_data"
        if completed:
            avg_score = round(
                sum(s.overall_score for s in completed) / len(completed), 1
            )
            if total_sessions >= TREND_MIN_SESSIONS:
                recent = completed[-TREND_RECENT_N:]
                earlier = completed[:-TREND_RECENT_N]
                if earlier:
                    recent_avg = sum(s.overall_score for s in recent) / len(recent)
                    earlier_avg = sum(s.overall_score for s in earlier) / len(earlier)
                    diff = recent_avg - earlier_avg
                    if diff > 2:
                        trend = "improving"
                    elif diff < -2:
                        trend = "declining"
                    else:
                        trend = "flat"

        overview = ProgressOverview(
            total_sessions=total_sessions,
            average_score=avg_score,
            trend=trend,
        )

        # --- by_role ---
        role_map: Dict[str, dict] = {}
        for s in all_sessions:
            key = s.job_role_normalized or "_unknown_"
            display = s.job_title or None
            if key not in role_map:
                role_map[key] = {
                    "sessions": [],
                    "display": display or key,
                }
            role_map[key]["sessions"].append(s)

        by_role = []
        for key, entry in role_map.items():
            role_sessions = entry["sessions"]
            sc = len(role_sessions)
            scored = [s for s in role_sessions if s.overall_score is not None]
            role_avg = (
                round(sum(s.overall_score for s in scored) / len(scored), 1)
                if scored else None
            )
            last_at = role_sessions[-1].created_at.isoformat() if role_sessions[-1].created_at else None

            role_trend = "not_enough_data"
            if sc >= TREND_MIN_SESSIONS:
                recent = role_sessions[-TREND_RECENT_N:]
                earlier = role_sessions[:-TREND_RECENT_N]
                if earlier and scored:
                    rev_avg = sum(s.overall_score for s in recent if s.overall_score is not None) / max(len([s for s in recent if s.overall_score is not None]), 1)
                    eav_avg = sum(s.overall_score for s in earlier if s.overall_score is not None) / max(len([s for s in earlier if s.overall_score is not None]), 1)
                    diff = rev_avg - eav_avg
                    if diff > 2:
                        role_trend = "improving"
                    elif diff < -2:
                        role_trend = "declining"
                    else:
                        role_trend = "flat"

            by_role.append(ProgressByRoleItem(
                job_role_normalized=key,
                job_role=entry["display"],
                session_count=sc,
                average_score=role_avg,
                last_practiced_at=last_at,
                trend=role_trend,
            ))

        sort_map = {
            "score_asc": lambda x: (x.average_score if x.average_score is not None else 999, x.job_role_normalized),
            "score_desc": lambda x: (-(x.average_score if x.average_score is not None else -999), x.job_role_normalized),
            "recent": lambda x: (x.last_practiced_at or "1900", x.job_role_normalized),
            "session_count": lambda x: (-x.session_count, x.job_role_normalized),
        }
        by_role.sort(key=sort_map.get(sort, sort_map["score_asc"]))

        # --- by_category ---
        KNOWN_CATEGORIES = ["Technical", "Behavioral", "HR", "Aptitude", "Communication"]
        cat_map: Dict[str, dict] = {c: {"count": 0, "scores": []} for c in KNOWN_CATEGORIES}

        for s in all_sessions:
            questions_raw = _parse_json_list(s.questions)
            answers_raw = _parse_json_list(s.answers)
            if not questions_raw or not answers_raw:
                continue
            answer_map = {}
            for a in answers_raw:
                qid = a.get("questionId") or a.get("question_id")
                if qid:
                    answer_map[qid] = a
            for q in questions_raw:
                cat = q.get("category", "Technical")
                if cat not in cat_map:
                    cat_map[cat] = {"count": 0, "scores": []}
                a = answer_map.get(q.get("id"))
                if a and not a.get("skipped", False) and a.get("answer", "").strip():
                    cat_map[cat]["count"] += 1
                    ev = a.get("evaluation")
                    if ev and not ev.get("evaluation_failed", False) and ev.get("score") is not None:
                        cat_map[cat]["scores"].append(ev["score"])

        by_category = []
        for cat in KNOWN_CATEGORIES:
            info = cat_map[cat]
            avg_cat = round(sum(info["scores"]) / len(info["scores"]), 1) if info["scores"] else None
            if info["count"] > 0 or info["scores"]:
                by_category.append(ProgressByCategoryItem(
                    category=cat,
                    question_count=info["count"],
                    average_score=avg_cat,
                ))

        return ProgressResponse(
            overview=overview,
            by_role=by_role,
            by_category=by_category,
        )


def _parse_json_list(value: Optional[str]) -> Optional[List]:
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _session_to_detail(session: InterviewSession) -> SessionDetail:
    skills_raw = _parse_json_list(session.skills)
    questions_raw = _parse_json_list(session.questions)
    questions = []
    if questions_raw:
        for q in questions_raw:
            questions.append(GeneratedQuestion(**q))

    started_str = session.started_at.isoformat() if session.started_at else None
    completed_str = session.completed_at.isoformat() if session.completed_at else None
    created_str = session.created_at.isoformat() if session.created_at else None

    return SessionDetail(
        id=session.id,
        session_type=session.session_type or SESSION_TYPE_PRACTICE,
        job_title=session.job_title,
        company_name=session.company_name,
        skills=skills_raw,
        difficulty=session.difficulty,
        question_count=session.question_count,
        questions=questions,
        answers=_parse_json_list(session.answers),
        overall_score=session.overall_score,
        how_it_went=session.how_it_went,
        self_rated_confidence=session.self_rated_confidence,
        questions_asked=session.questions_asked,
        related_job_application_id=session.related_job_application_id,
        started_at=started_str,
        completed_at=completed_str,
        created_at=created_str,
    )
