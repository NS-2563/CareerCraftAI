"""Deterministic cover-letter version diff.

Computes real text differences between two versions of a cover letter using the
standard-library ``difflib`` SequenceMatcher at line granularity. Every field in
the result is a computed fact (line/word counts, added/removed lines) — never an
AI narration of what changed.
"""

import difflib


def _operations(from_text: str, to_text: str) -> list:
    """Return the non-equal diff operations between two texts.

    Each entry is ``{"type": "insert"|"delete"|"replace", "removed": [...],
    "added": [...]}`` where ``removed``/``added`` hold the actual line fragments.
    """
    from_lines = (from_text or "").splitlines()
    to_lines = (to_text or "").splitlines()

    matcher = difflib.SequenceMatcher(a=from_lines, b=to_lines)
    ops = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        ops.append({
            "type": tag,  # "replace" | "delete" | "insert"
            "removed": from_lines[i1:i2],
            "added": to_lines[j1:j2],
        })
    return ops


def compute_cover_letter_diff(from_text: str, to_text: str) -> dict:
    """Deterministically compare two letter versions.

    Returns exactly the computed facts:
        from_line_count, to_line_count, lines_added, lines_removed,
        word_count_delta, changes
    """
    from_lines = (from_text or "").splitlines()
    to_lines = (to_text or "").splitlines()

    ops = _operations(from_text, to_text)

    added_lines = sum(
        len(op["added"]) for op in ops if op["type"] in ("insert", "replace")
    )
    removed_lines = sum(
        len(op["removed"]) for op in ops if op["type"] in ("delete", "replace")
    )
    from_words = len((from_text or "").split())
    to_words = len((to_text or "").split())

    return {
        "from_line_count": len(from_lines),
        "to_line_count": len(to_lines),
        "lines_added": added_lines,
        "lines_removed": removed_lines,
        "word_count_delta": to_words - from_words,
        "changes": ops,
    }
