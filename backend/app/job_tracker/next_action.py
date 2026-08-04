"""Deterministic "next recommended action" for a job application workspace.

This is NOT an AI suggestion. It is a fixed, documented decision tree evaluated
over real completion state (which fields exist, what is recorded for the
application). Given the same inputs it always returns the same recommendation.

Decision tree (first matching rule wins):

    R0. status in {Accepted, Rejected, Withdrawn}
            -> None (terminal application: nothing to recommend)
    R1. no saved job description
            -> "save_job_description"
            (JD match, Career Coach and Interview Prep all require it)
    R2. no linked resume
            -> "link_resume"
            (JD match and the cover letter generator need a resume)
    R3. no JD match recorded
            -> "run_jd_match"
    R4. no cover letter created
            -> "generate_cover_letter"
    R5. status is an active-pursuit status AND no communication logged AND
        it has been more than FOLLOW_UP_AFTER_DAYS days since applying
            -> "send_follow_up"
    R6. status is an interview-scheduled status AND no interview activity
        (real interview log or practice session) exists
            -> "practice_interview"
    R7. otherwise
            -> None (all readiness steps complete)
"""

from typing import Optional

# Follow-up threshold in days (matches the communication suggestions cron's
# 7-day staleness window).
FOLLOW_UP_AFTER_DAYS = 7

TERMINAL_STATUSES = frozenset({"Accepted", "Rejected", "Withdrawn"})

# Statuses where the application is being actively pursued (applied and still
# in play). A follow-up recommendation only makes sense in these states.
ACTIVE_PURSUIT_STATUSES = frozenset({"Applied", "Interview", "Interview Scheduled", "Offer"})

# Statuses where an interview is on the calendar or in progress, so practicing
# is the highest-value next step.
INTERVIEW_STATUSES = frozenset({"Interview", "Interview Scheduled"})


def recommend_next_action(state: dict) -> Optional[dict]:
    """Evaluate the decision tree over a completion-state dict.

    ``state`` keys (all booleans unless noted):
        status                 str   -- the application status
        has_job_description    bool  -- a trimmed job description is saved
        has_resume             bool  -- a resume is linked to the application
        has_jd_match           bool  -- a JD match result is recorded
        has_cover_letter       bool  -- at least one cover letter exists
        has_communication      bool  -- at least one communication message exists
        has_interview_activity bool  -- a real interview log OR practice session
        days_since_applied     Optional[int] -- whole days since applied_date
                                                 (or created_at), None when unknown

    Returns an action dict or None. The action dict has a stable ``key`` plus
    presentation fields; ``tab`` is the workspace section to surface.
    """
    status = state.get("status") or ""
    status_key = status.strip()

    if status_key in TERMINAL_STATUSES:
        return None

    if not state.get("has_job_description"):
        return _action(
            key="save_job_description",
            title="Save the job description",
            description=(
                "Resume Match, the Career Coach, and Interview Prep all need a "
                "saved job description. Add one to unlock everything for this role."
            ),
            cta="Save job description",
            tab="jd-match",
        )

    if not state.get("has_resume"):
        return _action(
            key="link_resume",
            title="Link a resume",
            description=(
                "Link the resume you used for this application so Resume Match and "
                "the cover letter generator can use it."
            ),
            cta="Link resume",
            tab="resume",
        )

    if not state.get("has_jd_match"):
        return _action(
            key="run_jd_match",
            title="Run Resume Match",
            description=(
                "Compare your linked resume against the saved job description to "
                "see how well you match and what skills to highlight."
            ),
            cta="Run match",
            tab="jd-match",
        )

    if not state.get("has_cover_letter"):
        return _action(
            key="generate_cover_letter",
            title="Generate a cover letter",
            description=(
                "A tailored cover letter for this role helps you stand out. Write "
                "one now using your resume and the job details."
            ),
            cta="Generate cover letter",
            tab="cover-letter",
        )

    days = state.get("days_since_applied")
    if (
        status_key in ACTIVE_PURSUIT_STATUSES
        and not state.get("has_communication")
        and days is not None
        and days > FOLLOW_UP_AFTER_DAYS
    ):
        return _action(
            key="send_follow_up",
            title="Send a follow-up",
            description=(
                f"It's been {days} days since you applied and no outreach is logged "
                "for this application. A polite follow-up keeps you top of mind."
            ),
            cta="Open communication",
            tab="communication",
        )

    if (
        status_key in INTERVIEW_STATUSES
        and not state.get("has_interview_activity")
    ):
        return _action(
            key="practice_interview",
            title="Schedule mock interview practice",
            description=(
                "An interview is on the calendar for this role and you haven't "
                "practiced or logged one yet. Run a mock session to prepare."
            ),
            cta="Practice",
            tab="interview",
        )

    return None


def _action(key: str, title: str, description: str, cta: str, tab: str) -> dict:
    return {
        "key": key,
        "title": title,
        "description": description,
        "cta": cta,
        "tab": tab,
    }
