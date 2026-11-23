from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.services.time import format_local, parse_local_datetime, to_local, to_utc


def test_parse_local_datetime_converts_to_utc() -> None:
    utc = parse_local_datetime("2026-11-23 08:00")
    expected = datetime(2026, 11, 23, 8, 0, tzinfo=ZoneInfo("Asia/Tehran")).astimezone(UTC)
    assert utc == expected


def test_round_trip_utc_local_utc() -> None:
    utc = datetime(2026, 11, 23, 4, 30, tzinfo=UTC)
    assert to_utc(to_local(utc)) == utc


def test_format_local() -> None:
    utc = datetime(2026, 11, 23, 4, 30, tzinfo=UTC)
    assert format_local(utc) == "2026-11-23 08:00"


def test_format_local_none() -> None:
    assert format_local(None) == "—"
