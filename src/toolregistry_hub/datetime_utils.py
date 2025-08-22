"""DateTime utilities for current time and timezone conversion.

Provides simple datetime functionality for LLM tools with timezone support.
"""

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
    
    All methods are static and can be used without instantiation.
    """

    @staticmethod
    def now(timezone_name: Optional[str] = None) -> str:
        """Get current time in ISO 8601 format.
        
        Args:
            timezone_name: Optional IANA timezone name (e.g., "Asia/Shanghai").
                          Defaults to UTC if None.
                          
        Raises:
            ValueError: If timezone is invalid.
        """
        if timezone_name:
            try:
                tz = ZoneInfo(timezone_name)
                dt = datetime.now(tz).replace(microsecond=0)
            except Exception as e:
                raise ValueError(f"Invalid timezone: {timezone_name}") from e
        else:
            dt = datetime.now(timezone.utc).replace(microsecond=0)

        return dt.isoformat()

    @staticmethod
    def convert_timezone(
        time_str: str, source_timezone: str, target_timezone: str
    ) -> Dict[str, Any]:
        """Convert time between IANA timezones.
        
        Args:
            time_str: Time in 24-hour format (HH:MM)
            source_timezone: Source timezone (e.g., "America/Chicago")
            target_timezone: Target timezone (e.g., "Asia/Shanghai")
            
        Returns:
            Dict with source_time, target_time, time_difference, and timezone info.
            
        Raises:
            ValueError: If timezone or time format is invalid.
        """
        # Validate and get timezone objects
        try:
            source_tz = ZoneInfo(source_timezone)
            target_tz = ZoneInfo(target_timezone)
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
