"""Timezone helpers.

All datetimes are persisted in UTC; the configured timezone (default Asia/Tehran)
is applied only at the boundary — when parsing user input or formatting output.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.config import get_settings


def get_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def now_utc() -> datetime:
    return datetime.now(UTC)


def now_local() -> datetime:
    return datetime.now(get_tz())


def local_date() -> date:
    return now_local().date()


def to_utc(dt: datetime) -> datetime:
    """Convert an aware datetime to UTC; a naive datetime is assumed to be local time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=get_tz())
    return dt.astimezone(UTC)


def to_local(dt: datetime) -> datetime:
    """Convert an aware datetime to the configured timezone; naive input is assumed UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(get_tz())


def parse_local_datetime(text: str) -> datetime:
    """Parse ``YYYY-MM-DD HH:MM`` as local time and return an aware UTC datetime."""
    naive = datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")
    return to_utc(naive)


def format_local(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return to_local(dt).strftime("%Y-%m-%d %H:%M")
