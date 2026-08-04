"""Shared helpers for versioned entities (resumes, cover letters, messages).

Every versioned entity stores a ``version_history`` JSON column whose entries
are snapshots of the form::

    {
        "version": int,
        "timestamp": iso-string,
        "note": str | None,
        "data": {...},
    }

These helpers centralize the snapshot/history bookkeeping that was previously
duplicated in ``resume_service``, ``cover_letter_service`` and the
communication service.
"""

from datetime import datetime

from app.utils.json_utils import to_json, from_json


VERSION_HISTORY_LIMIT = 50


def utcnow_iso() -> str:
    """Current UTC time as an ISO-8601 string."""
    return datetime.utcnow().isoformat()


def create_version_snapshot(entity, data: dict, note: str = None) -> dict:
    """Build a version snapshot for an entity."""
    return {
        "version": entity.version,
        "timestamp": utcnow_iso(),
        "note": note,
        "data": data,
    }


def get_version_history(version_history) -> list:
    """Parse a ``version_history`` column into a list of snapshots."""
    return from_json(version_history) if version_history else []


def record_version(entity, snapshot: dict) -> None:
    """Append a snapshot to an entity's history, keeping the last N entries."""
    history = get_version_history(entity.version_history)
    history.append(snapshot)
    entity.version_history = to_json(history[-VERSION_HISTORY_LIMIT:])


def find_version(history: list, version: int):
    """Return the snapshot matching ``version``, or ``None``."""
    for snapshot in history:
        if snapshot.get("version") == version:
            return snapshot
    return None
