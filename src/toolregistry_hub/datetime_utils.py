"""DateTime utilities module providing current date and time information.

This module provides simple datetime functionality for LLM function calling,
focusing on current time retrieval in ISO format.

Example:
    >>> from toolregistry_hub import DateTime
    >>> current_time = DateTime.now()
"""

from datetime import datetime, timezone


class DateTime:
    """Provides current date and time information for LLM function calling.
    
    This class offers simple datetime functionality focused on providing
    current time information in ISO format, which is ideal for LLM tools
    that need to know the current date and time.
    
    All methods are static and can be used without instantiation.
    """

    @staticmethod
    def now() -> str:
        """Get current UTC time in ISO 8601 format.
        
        Returns:
            str: Current UTC time in ISO 8601 format (e.g., "2025-08-11T07:07:34.700Z").
        """
        return datetime.now(timezone.utc).isoformat()