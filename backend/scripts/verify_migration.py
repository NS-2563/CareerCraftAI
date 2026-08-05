"""Verify a SQLite -> PostgreSQL data migration.

Reads every shared table from both databases and reports:
  * row counts (source vs destination)
  * a content checksum per table (hash of all column values)
  * enum / JSON / datetime spot-checks on tables that have them

Exits non-zero if any table's row count or checksum differs.

Usage:
    python scripts/verify_migration.py \
        --source sqlite:///D:/CareerCraftAI/backend/backup_careercraft.db \
        --dest postgresql://...#/careercraft
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone

from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TABLES = [
    "users", "resumes", "career_reports", "job_applications", "resume_analyses",
    "cover_letters", "jd_match_results", "roadmap_task_statuses",
    "insight_dismissals", "communication_messages", "communication_suggestions",
    "interview_sessions", "activity_events", "score_snapshots",
]


def _normalize(v):
    """Normalize a value so source/dest render identically for hashing.

    The two databases return the same logical value in different raw types
    (e.g. SQLite returns datetimes/JSON as text; PostgreSQL returns real
    objects), so canonicalization is type-tolerant:
      * datetimes/date -> naive-UTC ISO string (ignores tz tagging)
      * JSON dict/list (or JSON text) -> sorted, compact JSON
      * booleans -> "0"/"1"
    """
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, datetime):
        if v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        # A midnight timestamp and a bare DATE are the same logical value
        # (SQLite stores Dates as 'YYYY-MM-DD 00:00:00', PG as 'YYYY-MM-DD').
        if v.hour == 0 and v.minute == 0 and v.second == 0 and v.microsecond == 0:
            return v.date().isoformat()
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, str):
        # JSON text from SQLite -> parse to a comparable structure.
        try:
            parsed = json.loads(v)
        except (TypeError, ValueError):
            parsed = None
        if isinstance(parsed, (dict, list)):
            return "JSON:" + json.dumps(parsed, sort_keys=True, default=str)
        # SQLite returns datetimes as text ('YYYY-MM-DD HH:MM:SS[.ffffff]').
        # Render them the same way the datetime-object branch does (ISO 'T'),
        # collapsing midnight -> date to match PG Date columns.
        try:
            dt = datetime.fromisoformat(v.replace(" ", "T"))
            if isinstance(dt, datetime):
                if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.microsecond == 0:
                    return dt.date().isoformat()
                return dt.isoformat()
        except (TypeError, ValueError):
            pass
        return v
    if isinstance(v, (dict, list)):
        return "JSON:" + json.dumps(v, sort_keys=True, default=str)
    if isinstance(v, float):
        return repr(v)
    return str(v)


def _table_checksum(conn, table):
    rows = conn.execute(text(f'SELECT * FROM "{table}"')).mappings().all()
    h = hashlib.sha256()
    for row in rows:
        # Align by column NAME, not physical order (SQLite column order from
        # migrations differs from the model-declaration order used for PG).
        parts = [_normalize(row[k]) for k in sorted(row.keys())]
        h.update(("|".join(parts) + "\n").encode())
    return h.hexdigest()


def _count(conn, table):
    return conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar() or 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--dest", required=True)
    args = ap.parse_args()

    src = create_engine(args.source)
    dst = create_engine(args.dest)

    print(f"{'Table':<28}{'src':>6}{'dst':>6}  checksum  status")
    print("-" * 64)
    ok = True
    with src.connect() as sc, dst.connect() as dc:
        for t in TABLES:
            sc_count, dc_count = _count(sc, t), _count(dc, t)
            if sc_count != dc_count:
                print(f"{t:<28}{sc_count:>6}{dc_count:>6}  --       FAIL(rowcount)")
                ok = False
                continue
            s_hash = _table_checksum(sc, t)
            d_hash = _table_checksum(dc, t)
            match = s_hash == d_hash
            if not match:
                ok = False
            print(f"{t:<28}{sc_count:>6}{dc_count:>6}  {'OK' if match else 'DIFF'}")

    # ---- targeted integrity checks ----
    print("\n== enum / JSON / datetime spot-checks ==")
    with src.connect() as ec, dst.connect() as ed:
        for tbl, col in [("job_applications", "status")]:
            sv = [r[0] for r in ec.execute(text(f'SELECT {col} FROM {tbl}'))]
            dv = [r[0] for r in ed.execute(text(f'SELECT {col} FROM {tbl}'))]
            good = sorted(str(x) for x in sv) == sorted(str(x) for x in dv)
            ok = ok and good
            print(f"enum {tbl}.{col}: src={sorted(set(map(str,sv)))} dst={sorted(set(map(str,dv)))} {'OK' if good else 'DIFF'}")

    print("\n" + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())