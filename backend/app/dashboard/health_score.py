"""Career Health Score — a disclosed, reproducible weighted formula over real
sub-metrics only. Never AI-invented and never fabricated from a missing metric.

The score is the weighted arithmetic mean of whatever real sub-metrics a user
has, each clamped to a 0..100 scale:

    Sub-metric          Weight   Source                                          Available when
    ATS / resume score   0.40    latest real ``ats_score`` score snapshot        a snapshot exists
    Interview average    0.30    mean overall_score of completed PRACTICE        >= MIN_INTERVIEW_SESSIONS (3)
                                 sessions (real-interview logs excluded)         completed sessions
    JD-match coverage    0.30    mean latest per-application JDMatchResult       at least one stored match
                                 match_score (each app's newest result only)

    Score = sum(sub_metric_value * effective_weight)
    where effective_weight = weight / sum(weights of AVAILABLE sub-metrics).

Weights are chosen so a strong resume is the most important contributor (40%),
with interview skill and application fit each worth 30%.

Honest degradation rules (never a misleadingly precise number from nothing):
  * A sub-metric is omitted (and its weight redistributed proportionally to the
    remaining available sub-metrics) when it has no real backing value.
  * If FEWER than MIN_SUB_METRICS (2) real sub-metrics are available, the health
    score is explicitly "not enough data yet" — score is None, never a 0 or a
    placeholder. A single metric is not representative enough to call a score.

The response always includes the per-sub-metric value/availability/weight so the
number is fully explainable to a user.
"""

from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.analytics.service import AnalyticsService
from app.interview_prep.models import InterviewSession
from app.interview_prep.service import SESSION_TYPE_PRACTICE
from app.models.jd_match_result import JDMatchResult

# Documented weights and thresholds (single source of truth).
WEIGHTS = {
    "ats": 0.40,
    "interview": 0.30,
    "jd_match": 0.30,
}

LABELS = {
    "ats": "ATS / Resume score",
    "interview": "Interview average",
    "jd_match": "JD-match coverage",
}

MIN_SUB_METRICS = 2  # fewer than this available -> "not enough data yet"
MIN_INTERVIEW_SESSIONS = 3  # fewer completed practice sessions -> interview metric unavailable
MIN_JD_RECORDS = 1  # fewer JD-match records -> jd metric unavailable


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _ats_value(db: Session, user_id: int) -> Optional[float]:
    """Latest real ATS score, or None when the user has never been scored."""
    hist = AnalyticsService.get_history(
        db, user_id, "ats_score", limit=1, descending=True
    )
    if not hist:
        return None
    return round(_clamp(float(hist[0].value)), 1)


def _interview_value(db: Session, user_id: int) -> Optional[float]:
    """Average overall_score of completed practice sessions (real interviews
    excluded), or None when fewer than MIN_INTERVIEW_SESSIONS completed."""
    practice = or_(
        InterviewSession.session_type == SESSION_TYPE_PRACTICE,
        InterviewSession.session_type.is_(None),
    )
    row = (
        db.query(
            func.count(InterviewSession.id),
            func.avg(InterviewSession.overall_score),
        )
        .filter(
            InterviewSession.user_id == user_id,
            practice,
            InterviewSession.overall_score != None,
        )
        .one()
    )
    count, avg = row[0] or 0, row[1]
    if count < MIN_INTERVIEW_SESSIONS or avg is None:
        return None
    return round(_clamp(float(avg)), 1)


def _jd_value(db: Session, user_id: int) -> Optional[float]:
    """Average of each application's LATEST JD match score.

    Only the most recent JDMatchResult per application is counted (so repeated
    re-runs don't double-weight one application), then averaged.
    """
    rows = (
        db.query(JDMatchResult)
        .filter(JDMatchResult.user_id == user_id)
        .order_by(JDMatchResult.created_at.desc(), JDMatchResult.id.desc())
        .all()
    )
    seen = {}
    for r in rows:
        if r.job_application_id is not None and r.job_application_id not in seen:
            seen[r.job_application_id] = r.match_score
    scores = [_clamp(float(s)) for s in seen.values()]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


_VALUE_RESOLVERS = {
    "ats": _ats_value,
    "interview": _interview_value,
    "jd_match": _jd_value,
}


def compute_career_health_score(db: Session, user_id: int) -> dict:
    """Compute the disclosed Career Health Score for a user.

    Returns a fully-explainable dict: the overall score (or an explicit
    "not enough data yet" state) plus every sub-metric's value, weight, and
    effective weight after redistribution.
    """
    sub_metrics = []
    for key in ("ats", "interview", "jd_match"):
        value = _VALUE_RESOLVERS[key](db, user_id)
        sub_metrics.append({
            "key": key,
            "label": LABELS[key],
            "available": value is not None,
            "value": value,
            "weight": WEIGHTS[key],
            "effective_weight": None,
        })

    available = [m for m in sub_metrics if m["available"]]

    base = {
        "labels": dict(LABELS),
        "weights": dict(WEIGHTS),
        "minimum_sub_metrics": MIN_SUB_METRICS,
        "sub_metrics": sub_metrics,
    }

    if len(available) < MIN_SUB_METRICS:
        return {
            **base,
            "available": False,
            "score": None,
            "reason": "not enough data yet",
            "minimum_sub_metric_reason": (
                "At least {0} real sub-metrics are required before a Career "
                "Health Score is shown. Current available: {1}.".format(
                    MIN_SUB_METRICS, len(available)
                )
            ),
        }

    total_weight = sum(m["weight"] for m in available)
    weighted_sum = 0.0
    for m in available:
        effective = m["weight"] / total_weight
        m["effective_weight"] = round(effective, 4)
        weighted_sum += m["value"] * effective

    return {
        **base,
        "available": True,
        "score": round(weighted_sum, 1),
        "reason": None,
    }