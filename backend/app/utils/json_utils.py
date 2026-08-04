"""Shared JSON serialization helpers.

Consolidates the ``_to_json`` / ``_from_json`` pairs that were previously
duplicated in several service modules.
"""

import json


def to_json(data) -> str:
    """Convert dict/list to JSON string, defaulting to an empty list."""
    if data is None:
        return "[]"
    try:
        return json.dumps(data)
    except Exception:
        return "[]"


def from_json(text) -> dict:
    """Convert JSON string to dict, defaulting to an empty dict."""
    if text:
        try:
            return json.loads(text)
        except Exception:
            pass
    return {}
