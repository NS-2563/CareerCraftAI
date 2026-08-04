import json

from sqlalchemy.orm import Session

from app.models.career_report import CareerReport
from app.models.jd_match_result import JDMatchResult

MIN_SKILL_GAP_SAMPLE_SIZE = 3
SKILL_GAP_TOP_N = 5


def _extract_missing_skill_names(raw: str):
    """Parse a stored missing_skills JSON column into a list of skill names.

    ``missing_skills`` is serialized as a JSON list of skill item dicts (each
    with a ``name`` key) or plain strings.  Anything unparseable is skipped so
    a single malformed row can never poison the tally.
    """
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []

    if not isinstance(parsed, list):
        return []

    names = []
    for item in parsed:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name:
                names.append(name)
        elif isinstance(item, str) and item:
            names.append(item)
    return names


def get_skill_gap_summary(
    db: Session,
    user_id: int,
    min_sample_size: int = MIN_SKILL_GAP_SAMPLE_SIZE,
    top_n: int = SKILL_GAP_TOP_N,
) -> dict:
    """Compute a real skill-gap insight from the user's own stored JD matches.

    Tally how often each missing skill appears across the user's
    ``JDMatchResult`` rows (one per saved application match) and return the
    most frequently missing skills ranked by occurrence count.

    Below ``min_sample_size`` stored results there is not enough signal for a
    meaningful insight, so an explicit ``insufficient_data`` response is
    returned instead of a misleading tally.  Only the user's own rows are ever
    considered — no external market data is consulted.
    """
    rows = (
        db.query(JDMatchResult)
        .filter(JDMatchResult.user_id == user_id)
        .order_by(JDMatchResult.created_at.asc(), JDMatchResult.id.asc())
        .all()
    )

    total_applications = len(rows)

    if total_applications < min_sample_size:
        return {
            "has_data": False,
            "insufficient_data": True,
            "total_applications": total_applications,
            "min_sample_size": min_sample_size,
            "message": (
                "Not enough JD match data yet. Save at least "
                f"{min_sample_size} job description matches to see a real "
                "skill gap insight."
            ),
            "top_missing_skills": [],
        }

    frequency = {}
    for row in rows:
        for name in _extract_missing_skill_names(row.missing_skills):
            frequency[name] = frequency.get(name, 0) + 1

    top_skills = sorted(
        frequency.items(),
        key=lambda item: (-item[1], item[0]),
    )[:top_n]

    return {
        "has_data": True,
        "insufficient_data": False,
        "total_applications": total_applications,
        "min_sample_size": min_sample_size,
        "top_missing_skills": [
            {"name": name, "count": count}
            for name, count in top_skills
        ],
    }


def get_analytics(db, user_id: int):
    reports = (
        db.query(CareerReport)
        .filter(CareerReport.user_id == user_id)
        .order_by(CareerReport.created_at.asc())
        .all()
    )

    if not reports:
        return {
            "total_reports": 0,
            "average_score": 0,
            "highest_score": 0,
            "latest_score": 0,
            "previous_score": None,
            "score_change": None,
            "career_goals": {},
            "trend": [],
        }

    scores = [report.readiness_score for report in reports]

    goal_counts = {}

    for report in reports:
        goal = report.career_goal

        if goal not in goal_counts:
            goal_counts[goal] = 0

        goal_counts[goal] += 1

    trend = []

    for report in reports:
        trend.append(
            {
                "date": report.created_at.strftime("%d %b %H:%M"),
                "score": report.readiness_score,
            }
        )

    latest_score = scores[-1]

    previous_score = None
    score_change = None

    if len(scores) >= 2:
        previous_score = scores[-2]
        score_change = latest_score - previous_score

    return {
        "total_reports": len(reports),
        "average_score": round(sum(scores) / len(scores), 1),
        "highest_score": max(scores),
        "latest_score": latest_score,
        "previous_score": previous_score,
        "score_change": score_change,
        "career_goals": goal_counts,
        "trend": trend,
    }