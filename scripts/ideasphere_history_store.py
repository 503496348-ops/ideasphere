from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_DEFAULT = Path('~/.ideasphere_doctor_cache/doctor_runs.sqlite').expanduser()


def connect(db_path: str | Path = DB_DEFAULT):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path.as_posix())
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS doctor_runs(
            run_id TEXT PRIMARY KEY,
            checked_at TEXT NOT NULL,
            passed INTEGER NOT NULL,
            checks_total INTEGER NOT NULL,
            failed_checks INTEGER NOT NULL,
            summary TEXT NOT NULL
        )
        '''
    )
    conn.commit()
    return conn


def save_run(run_id: str, checks: list[dict[str, Any]], passed: bool, db_path: str | Path = DB_DEFAULT) -> tuple[str, int, int]:
    total = len(checks)
    failed = len([c for c in checks if not c.get('ok')])
    summary = (', '.join(c.get('name', '') for c in checks if not c.get('ok')) or 'all_clear')[:320]
    checked_at = datetime.utcnow().isoformat() + 'Z'

    conn = connect(db_path)
    conn.execute(
        'INSERT OR REPLACE INTO doctor_runs (run_id, checked_at, passed, checks_total, failed_checks, summary) VALUES (?, ?, ?, ?, ?, ?)',
        (run_id, checked_at, 1 if passed else 0, total, failed, summary),
    )
    conn.commit()
    conn.close()
    return run_id, total, failed


def latest_runs(limit: int = 20, db_path: str | Path = DB_DEFAULT) -> list[dict[str, Any]]:
    conn = connect(db_path)
    rows = conn.execute(
        'SELECT run_id, checked_at, passed, checks_total, failed_checks, summary FROM doctor_runs ORDER BY checked_at DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return [
        {
            'run_id': r[0],
            'checked_at': r[1],
            'passed': bool(r[2]),
            'checks_total': r[3],
            'failed_checks': r[4],
            'summary': r[5],
        }
        for r in rows
    ]