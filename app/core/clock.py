"""The only place that reads the clock. Tests patch these functions."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def now_iso() -> str:
    """Entry time as UTC ISO 8601 text, for example 2026-11-05T10:00:00Z."""
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def today_iso() -> str:
    return utc_now().date().isoformat()  # the server date in UTC
