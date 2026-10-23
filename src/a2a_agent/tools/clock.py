"""Tool that returns the current date and time."""

from __future__ import annotations

from datetime import UTC, datetime, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.tools import tool


@tool
def get_current_time(timezone_name: str = "UTC") -> str:
    """Return the current date and time in the given IANA time zone.

    Args:
        timezone_name: IANA time zone name such as "Europe/Madrid",
            "America/New_York" or "UTC". Defaults to "UTC".
    """
    tz: tzinfo
    try:
        tz = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        tz = UTC
        timezone_name = "UTC"

    now = datetime.now(tz)
    return now.strftime(f"%Y-%m-%d %H:%M:%S {timezone_name} (%A)")
