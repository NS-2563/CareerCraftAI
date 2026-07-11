from app.models.career_report import CareerReport


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