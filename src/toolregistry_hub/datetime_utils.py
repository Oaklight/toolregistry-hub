"""DateTime utilities for current time and timezone conversion.

Provides simple datetime functionality for LLM tools with timezone support.
Supports both IANA timezone names (e.g., "America/New_York") and
UTC/GMT offset formats (e.g., "UTC+5", "GMT-3", "UTC+5:30").
"""

import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

# Handle zoneinfo import with fallback for Python 3.8
if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo


class DateTime:
    """DateTime utilities for LLM tools with timezone support.

    Supports both IANA timezone names and UTC/GMT offset formats.
    All methods are static and can be used without instantiation.
    """

    @staticmethod
    def _parse_timezone_offset(timezone_str: str) -> timezone:
        """Parse UTC/GMT offset string into timezone object.

        Args:
            timezone_str: UTC/GMT offset string (e.g., "UTC+5", "GMT-3", "UTC+5:30")

        Returns:
            timezone object with the specified offset

        Raises:
            ValueError: If offset format is invalid
        """
        # Match patterns like UTC+5, GMT-3, UTC+5:30, GMT-3:45
        pattern = r"^(UTC|GMT)([+-])(\d{1,2})(?::(\d{2}))?$"
        match = re.match(pattern, timezone_str, re.IGNORECASE)

        if not match:
            raise ValueError(f"Invalid UTC/GMT offset format: {timezone_str}")

        sign = match.group(2)
        hours = int(match.group(3))
        minutes = int(match.group(4) or 0)

        if hours > 23 or minutes > 59:
            raise ValueError(f"Invalid time offset: {timezone_str}")

        total_minutes = hours * 60 + minutes
        if sign == "-":
            total_minutes = -total_minutes

        return timezone(timedelta(minutes=total_minutes))

    @staticmethod
    def _get_timezone_obj(tz_str: str):
        """Get timezone object from either IANA name or UTC/GMT offset.

        Args:
            tz_str: IANA timezone name or UTC/GMT offset string

        Returns:
            timezone object

        Raises:
            ValueError: If timezone format is invalid
        """
        # Handle special case for plain "UTC"
        if tz_str.upper() == "UTC":
            return timezone.utc

        # Check if it's a UTC/GMT offset format
        if tz_str.upper().startswith(("UTC", "GMT")):
            return DateTime._parse_timezone_offset(tz_str)

        # Otherwise treat as IANA timezone
        try:
            return ZoneInfo(tz_str)
        except Exception as e:
            raise ValueError(f"Invalid timezone: {tz_str}") from e

    @staticmethod
    def now(timezone_name: Optional[str] = None) -> str:
        """Get current time in ISO 8601 format.

        Args:
            timezone_name: Optional timezone name (e.g., "Asia/Shanghai", "UTC+5"). Defaults to UTC if None.

        Raises:
            ValueError: If timezone is invalid.
        """
        if timezone_name:
            tz = DateTime._get_timezone_obj(timezone_name)
            dt = datetime.now(tz).replace(microsecond=0)
        else:
            dt = datetime.now(timezone.utc).replace(microsecond=0)

        return dt.isoformat()

    @staticmethod
    def convert_timezone(
        time_str: str, source_timezone: str, target_timezone: str
    ) -> Dict[str, Any]:
        """Convert time between timezones.

        Args:
            time_str: Time in 24-hour format (HH:MM)
            source_timezone: Source timezone (e.g., "America/Chicago", "UTC+5")
            target_timezone: Target timezone (e.g., "Asia/Shanghai", "GMT-3")

        Returns:
            Dict with source_time, target_time, time_difference, and timezone info.

        Raises:
            ValueError: If timezone or time format is invalid.
        """
        # Validate and get timezone objects
        try:
            source_tz = DateTime._get_timezone_obj(source_timezone)
            target_tz = DateTime._get_timezone_obj(target_timezone)
        except Exception as e:
            raise ValueError(f"Invalid timezone: {str(e)}")

        # Parse time string (HH:MM format)
        try:
            parsed_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValueError("Invalid time format. Expected HH:MM [24-hour format]")

        # Get current date in source timezone and combine with parsed time
        now = datetime.now(source_tz)
        source_time = datetime(
            now.year,
            now.month,
            now.day,
            parsed_time.hour,
            parsed_time.minute,
            tzinfo=source_tz,
        ).replace(microsecond=0)

        # Convert to target timezone
        target_time = source_time.astimezone(target_tz)

        # Calculate time difference
        source_offset = source_time.utcoffset() or timedelta()
        target_offset = target_time.utcoffset() or timedelta()
        hours_difference = (target_offset - source_offset).total_seconds() / 3600

        # Format time difference string
        if hours_difference.is_integer():
            time_diff_str = f"{hours_difference:+.1f}h"
        else:
            # For fractional hours like Nepal's UTC+5:45
            time_diff_str = f"{hours_difference:+.2f}".rstrip("0").rstrip(".") + "h"

        return {
            "source_time": source_time.isoformat(),
            "target_time": target_time.isoformat(),
            "time_difference": time_diff_str,
            "source_timezone": source_timezone,
            "target_timezone": target_timezone,
        }
