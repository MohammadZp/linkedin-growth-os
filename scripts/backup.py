"""Backup and export helpers for the LinkedIn Growth OS database.

Run from the project root:

    .venv\\Scripts\\python scripts\\backup.py backup
    .venv\\Scripts\\python scripts\\backup.py export-json

``backup`` copies the SQLite database file using SQLite's online backup API, so it
is safe to run while the bot is live and produces a consistent snapshot.
``export-json`` dumps every table to a human-readable JSON file (a portable export
that is not tied to a specific SQLite version).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date, datetime, time
from pathlib import Path

from app.config import get_settings
from app.database import (
    get_engine,
    init_db,
    models,  # noqa: F401  (register tables on Base.metadata)
)
from app.database.base import Base
from sqlalchemy import make_url

BACKUP_DIR = Path("backups")


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _sqlite_path(database_url: str) -> Path | None:
    """Return the filesystem path for a file-based SQLite database, or None."""
    if not database_url.startswith("sqlite"):
        return None
    database = make_url(database_url).database
    if not database or database == ":memory:":
        return None
    return Path(database)


def backup_db() -> Path:
    """Copy the SQLite database file to ``backups/`` with a timestamp suffix."""
    path = _sqlite_path(get_settings().database_url)
    if path is None:
        raise SystemExit("backup only supports file-based SQLite databases.")
    if not path.exists():
        raise SystemExit(f"database file not found: {path}")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    destination = BACKUP_DIR / f"linkedin_growth_{_timestamp()}.db"

    source = sqlite3.connect(path)
    target = sqlite3.connect(destination)
    try:
        with target:
            source.backup(target)
    finally:
        target.close()
        source.close()
    return destination


def _json_default(value: object) -> str:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return str(value)


def export_json() -> Path:
    """Dump all tables to a single JSON file in ``backups/``."""
    init_db()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    destination = BACKUP_DIR / f"linkedin_growth_{_timestamp()}.json"

    payload: dict[str, list[dict]] = {}
    with get_engine().connect() as connection:
        for table in Base.metadata.sorted_tables:
            payload[table.name] = [dict(row._mapping) for row in connection.execute(table.select())]

    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Back up or export the LinkedIn Growth OS database."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="backup",
        choices=["backup", "export-json"],
        help="'backup' copies the SQLite file; 'export-json' dumps tables to JSON",
    )
    args = parser.parse_args()

    destination = backup_db() if args.command == "backup" else export_json()
    print(f"Wrote {destination} ({destination.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
