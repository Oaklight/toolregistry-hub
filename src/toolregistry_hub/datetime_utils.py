"""DateTime utilities module providing current date and time information.

This module provides simple datetime functionality for LLM function calling,
focusing on current time retrieval in ISO format with timezone support.

Example:
    >>> from toolregistry_hub import DateTime
    >>> current_time = DateTime.now()  # UTC time
    >>> current_time = DateTime.now("America/New_York")  # New York time
"""

import sys
from datetime import datetime, timezone
from typing import Optional

# Handle zoneinfo import with fallback for Python 3.8
if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo


class DateTime:
    """Provides current date and time information for LLM function calling.
    
    This class offers simple datetime functionality focused on providing
    current time information in ISO format, which is ideal for LLM tools
    that need to know the current date and time.
    
    All methods are static and can be used without instantiation.
    """

    @staticmethod
    def now(timezone_name: Optional[str] = None) -> str:
        """Get current time in ISO 8601 format.
        
        Args:
            timezone_name: Optional timezone name (e.g., "Asia/Shanghai", "America/Chicago").
                          If None, returns UTC time.
                
        Raises:
            ValueError: If the timezone name is invalid.
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