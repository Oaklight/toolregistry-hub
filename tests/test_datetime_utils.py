"""Unit tests for DateTime module."""

import re
from datetime import datetime

import pytest

from toolregistry_hub.datetime_utils import DateTime


class TestDateTime:
    """Test cases for DateTime class."""

    def test_now(self):
        """Test now method returns current UTC time in ISO format."""
        result = DateTime.now()
        
        # Should be a string
        assert isinstance(result, str)
        
        # Should match ISO 8601 format with timezone info
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+00:00$'
        assert re.match(iso_pattern, result), f"Result '{result}' doesn't match ISO format"
        
        # Should be parseable as datetime
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None
        
        # Should be recent (within last minute)
        now = datetime.now(parsed.tzinfo)
        time_diff = abs((now - parsed).total_seconds())
        assert time_diff < 60, f"Time difference too large: {time_diff} seconds"

    def test_now_multiple_calls(self):
        """Test that multiple calls to now() return different but close times."""
        time1 = DateTime.now()
        time2 = DateTime.now()
        
        # Should be different strings (unless called at exact same microsecond)
        # But both should be valid ISO format
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+00:00$'
        assert re.match(iso_pattern, time1)
        assert re.match(iso_pattern, time2)
        
        # Parse both times
        parsed1 = datetime.fromisoformat(time1)
        parsed2 = datetime.fromisoformat(time2)
        
        # Second time should be same or later than first
        assert parsed2 >= parsed1