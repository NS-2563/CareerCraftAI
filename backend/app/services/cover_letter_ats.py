"""Deterministic ATS keyword coverage for cover letters.

Computes which of a job description's extracted keywords actually appear in a
generated cover letter's text. Deliberately reuses the exact keyword-extraction
logic from the deterministic JD matcher — ``_extract_keywords`` — so there is a
single source of truth for what counts as a "keyword". The result is a real
integer count, never an AI judgment of how well the letter covers the JD.
"""

from app.analysis.deterministic.jd_matcher import _extract_keywords


def compute_keyword_coverage(job_description, letter_content) -> dict:
    """Return which JD keywords appear in the letter.

    Args:
        job_description: Raw job description text (may be None/empty).
        letter_content: Generated cover letter text (may be None/empty).

    Returns:
        ``{
            "covered_keywords": [...],
            "missing_keywords": [...],
            "covered_count": int,
            "total_keywords": int,
            "label": str,
        }``

        When there is no job description, ``total_keywords`` is 0 and ``label``
        states that no JD is available to check against.
    """
    jd_keywords = _extract_keywords(job_description or "")
    letter_keywords = _extract_keywords(letter_content or "")

    jd_set = set(jd_keywords)
    letter_set = set(letter_keywords)

    covered = sorted(jd_set & letter_set)
    missing = sorted(jd_set - letter_set)
    total = len(jd_set)

    if total == 0:
        label = "No job description to check"
    else:
        label = f"{len(covered)} of {total} keywords present"

    return {
        "covered_keywords": covered,
        "missing_keywords": missing,
        "covered_count": len(covered),
        "total_keywords": total,
        "label": label,
    }
