"""Input validation helpers shared by services and handlers."""

from __future__ import annotations

from urllib.parse import urlparse


def is_valid_url(value: str | None) -> bool:
    """Return True when ``value`` is a plausible http(s) URL."""
    if not value:
        return False
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)
