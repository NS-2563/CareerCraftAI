def build_context(module: str, user_data: dict, db=None, user_id: int = None) -> str:
    """
    Build a standardized context for AI modules.

    Responsibilities:
    - Format user data consistently
    - Skip None values
    - Format lists cleanly
    - Preserve multiline text
    - Optionally enrich with real user signals (skill gaps from saved JD
      matches and weakest interview-prep category) when ``db``/``user_id``
      are provided.  These are additive and clearly labeled; absence of
      either signal is handled gracefully.
    """

    lines = [
        "You are CareerCraft AI.",
        "",
        "Application Module:",
        module,
        "",
        "User Information:",
    ]

    for key, value in user_data.items():

        if value is None:
            continue

        if isinstance(value, list):

            if not value:
                continue

            lines.append(f"{key}:")

            for item in value:
                lines.append(f"- {item}")

            continue

        value = str(value).strip()

        if not value:
            continue

        value = value.replace("\r\n", "\n")
        value = value.replace("\r", "\n")

        lines.append(f"{key}: {value}")

    if db is not None and user_id is not None:
        _append_real_user_signals(lines, db, user_id)

    lines.extend(
        [
            "",
            "General Instructions",
            "",
            "- Return accurate information.",
            "- Avoid unnecessary explanations.",
            "- Keep responses concise but complete.",
            "- Never hallucinate.",
            "- Return only the requested format.",
        ]
    )

    return "\n".join(lines)


def _append_real_user_signals(lines: list, db, user_id: int) -> None:
    """Append clearly-labeled, user-owned signal blocks to the context.

    All signals are optional and independently guarded — a missing one never
    breaks context assembly.  No external market data is involved.
    """
    lines.append("")
    lines.append("Real User Signals (computed from this user's own data):")

    skill_gap_block = _build_skill_gap_block(db, user_id)
    if skill_gap_block:
        lines.extend(skill_gap_block)
    else:
        lines.append("- Skill gaps: not enough saved JD matches yet (skipped).")

    interview_block = _build_weakest_interview_block(db, user_id)
    if interview_block:
        lines.extend(interview_block)
    else:
        lines.append("- Interview weaknesses: not enough practice data yet (skipped).")

    real_interview_block = _build_real_interview_block(db, user_id)
    if real_interview_block:
        lines.extend(real_interview_block)
    else:
        lines.append("- Real interviews: no real-interview logs yet (skipped).")


def _build_skill_gap_block(db, user_id: int) -> list:
    """Return labeled skill-gap lines, or [] when there's no real signal yet."""
    try:
        from app.career.services.analytics_service import get_skill_gap_summary

        summary = get_skill_gap_summary(db, user_id)
        if not summary.get("has_data") or not summary.get("top_missing_skills"):
            return []

        total = summary["total_applications"]
        block = [
            "Skill gaps from the user's own saved JD matches:",
            f"- considered applications: {total}",
        ]
        for skill in summary["top_missing_skills"]:
            block.append(
                f"- {skill['name']}: required in {skill['count']} of {total} "
                "applications, missing from resume"
            )
        return block
    except Exception:
        return []


def _build_weakest_interview_block(db, user_id: int) -> list:
    """Return labeled weakest-interview-category lines, or [] when unavailable.

    Requires enough practice data (at least the session floor) and a category
    with at least ``MIN_SCORED_QUESTIONS`` scored answers so the "weakest"
    label is grounded rather than a single-answer fluke.
    """
    MIN_SESSIONS = 2
    MIN_SCORED_QUESTIONS = 2

    try:
        from app.interview_prep.service import InterviewPrepService

        progress = InterviewPrepService.get_progress(db, user_id)
        if progress.overview.total_sessions < MIN_SESSIONS:
            return []

        candidates = [
            cat
            for cat in progress.by_category
            if cat.average_score is not None
            and cat.question_count >= MIN_SCORED_QUESTIONS
        ]
        if not candidates:
            return []

        weakest = min(candidates, key=lambda c: c.average_score)
        return [
            "Weakest interview category (from the user's own practice sessions):",
            (
                f"- {weakest.category}: average score {weakest.average_score} "
                f"across {weakest.question_count} scored answers"
            ),
        ]
    except Exception:
        return []


def _build_real_interview_block(db, user_id: int) -> list:
    """Return labeled real-interview log lines, or [] when there are none.

    Real-interview logs are a distinct, application-linked entry type. Their
    outcome is more informative than practice performance, so the block carries
    an explicit instruction that these signals outweigh practice scores when
    both are present.
    """
    try:
        from app.interview_prep.models import InterviewSession
        from app.interview_prep.service import SESSION_TYPE_REAL_INTERVIEW

        logs = (
            db.query(InterviewSession)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewSession.session_type == SESSION_TYPE_REAL_INTERVIEW,
            )
            .order_by(InterviewSession.created_at.desc(), InterviewSession.id.desc())
            .limit(5)
            .all()
        )
        if not logs:
            return []

        block = [
            "Real interview logs (from the user's own real interviews):",
            (
                "- Weighting: real interview outcomes are MORE informative than "
                "practice scores; when both exist, ground recommendations in the "
                "real interviews first."
            ),
        ]
        for s in logs:
            title = s.job_title or "Interview"
            heading = f"- {title}"
            if s.company_name:
                heading += f" at {s.company_name}"
            if s.self_rated_confidence is not None:
                heading += (
                    f" — self-rated confidence "
                    f"{round(float(s.self_rated_confidence))}/100"
                )
            block.append(heading)
            if s.how_it_went:
                block.append(f"  How it went: {s.how_it_went}")
            if s.questions_asked:
                block.append(f"  Questions asked: {s.questions_asked}")
        return block
    except Exception:
        return []