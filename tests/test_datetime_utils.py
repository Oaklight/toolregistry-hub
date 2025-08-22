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
        
        # Should match ISO 8601 format with timezone info (without microseconds)
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$'
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
        
        # Should be different strings (unless called at exact same second)
        # But both should be valid ISO format
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$'
        assert re.match(iso_pattern, time1)
        assert re.match(iso_pattern, time2)
        
        # Parse both times
        parsed1 = datetime.fromisoformat(time1)
        parsed2 = datetime.fromisoformat(time2)
        
        # Second time should be same or later than first
        assert parsed2 >= parsed1

    def test_now_with_timezone(self):
        """Test now() method with timezone parameter."""
        # Test with valid timezone
        result = DateTime.now("America/New_York")
        
        # Should be a string
        assert isinstance(result, str)
        
        # Should match ISO 8601 format with timezone offset
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'
        assert re.match(iso_pattern, result), f"Result '{result}' doesn't match ISO format with timezone"
        
        # Should be parseable as datetime
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None

    def test_now_with_utc_timezone(self):
        """Test now() method with UTC timezone explicitly."""
        result = DateTime.now("UTC")
        
        # Should be a string
        assert isinstance(result, str)
        
        # Should match ISO 8601 format with UTC timezone
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$'
        assert re.match(iso_pattern, result), f"Result '{result}' doesn't match UTC ISO format"

    def test_now_with_invalid_timezone(self):
        """Test now() method raises ValueError for invalid timezone."""
        with pytest.raises(ValueError, match="Invalid timezone"):
            DateTime.now("Invalid/Timezone")

    def test_now_backwards_compatibility(self):
        """Test that now() without arguments still works as before."""
        result = DateTime.now()
        
        # Should be a string
        assert isinstance(result, str)
        
        # Should match ISO 8601 format with UTC timezone
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$'
        assert re.match(iso_pattern, result), f"Result '{result}' doesn't match ISO format"
        
        # Should be parseable as datetime
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None

    def test_convert_time_basic(self):
        """Test basic time conversion between timezones."""
        result = DateTime.convert_timezone("14:30", "America/New_York", "Europe/London")
        
        # Should return a dictionary with expected keys
        assert isinstance(result, dict)
        expected_keys = {"source_time", "target_time", "time_difference", "source_timezone", "target_timezone"}
        assert set(result.keys()) == expected_keys
        
        # Timezone values should match input
        assert result["source_timezone"] == "America/New_York"
        assert result["target_timezone"] == "Europe/London"
        
        # Both times should be valid ISO format strings
        assert re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$', result["source_time"])
        assert re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$', result["target_time"])
        
        # Time difference should be a string ending with 'h'
        assert isinstance(result["time_difference"], str)
        assert result["time_difference"].endswith('h')

    def test_convert_time_same_timezone(self):
        """Test time conversion within the same timezone."""
        result = DateTime.convert_timezone("12:00", "UTC", "UTC")
        
        # Times should be identical (or very close due to processing time)
        source_dt = datetime.fromisoformat(result["source_time"])
        target_dt = datetime.fromisoformat(result["target_time"])
        
        # Time difference should be 0 hours
        assert result["time_difference"] == "+0.0h" or result["time_difference"] == "+0h"

    def test_convert_time_known_offset(self):
        """Test time conversion with known timezone offsets."""
        # New York to London should have positive time difference (London is ahead of New York)
        result = DateTime.convert_timezone("10:00", "America/New_York", "Europe/London")
        
        # The time difference should be positive (London is ahead of New York)
        assert result["time_difference"].startswith('+')
        
        # Parse the times to verify they're reasonable
        source_dt = datetime.fromisoformat(result["source_time"])
        target_dt = datetime.fromisoformat(result["target_time"])
        
        # The conversion should work correctly (times should be different timezones)
        assert source_dt.tzinfo != target_dt.tzinfo
        # Both should have timezone info
        assert source_dt.tzinfo is not None
        assert target_dt.tzinfo is not None

    def test_convert_time_invalid_timezone(self):
        """Test convert_time raises ValueError for invalid timezone."""
        with pytest.raises(ValueError, match="Invalid timezone"):
            DateTime.convert_timezone("12:00", "Invalid/Timezone", "UTC")
        
        with pytest.raises(ValueError, match="Invalid timezone"):
            DateTime.convert_timezone("12:00", "UTC", "Invalid/Timezone")

    def test_convert_time_invalid_time_format(self):
        """Test convert_time raises ValueError for invalid time format."""
        with pytest.raises(ValueError, match="Invalid time format"):
            DateTime.convert_timezone("25:00", "UTC", "UTC")  # Invalid hour
        
        with pytest.raises(ValueError, match="Invalid time format"):
            DateTime.convert_timezone("12:60", "UTC", "UTC")  # Invalid minute
        
        with pytest.raises(ValueError, match="Invalid time format"):
            DateTime.convert_timezone("12.30", "UTC", "UTC")  # Wrong format
        
        with pytest.raises(ValueError, match="Invalid time format"):
            DateTime.convert_timezone("12", "UTC", "UTC")  # Missing minutes

    def test_convert_time_edge_cases(self):
        """Test convert_time with edge cases like midnight."""
        # Test midnight conversion
        result = DateTime.convert_timezone("00:00", "UTC", "America/New_York")
        assert isinstance(result, dict)
        assert "source_time" in result
        assert "target_time" in result
        
        # Test noon conversion
        result = DateTime.convert_timezone("12:00", "UTC", "America/New_York")
        assert isinstance(result, dict)
        assert "source_time" in result
        assert "target_time" in result

    def test_convert_time_fractional_hours(self):
        """Test convert_time with timezones that have fractional hour offsets."""
        # Test with a timezone that has fractional hour offset (e.g., Nepal UTC+5:45)
        result = DateTime.convert_timezone("12:00", "UTC", "Asia/Kathmandu")
        
        # Should handle fractional hours properly
        assert isinstance(result["time_difference"], str)
        assert result["time_difference"].endswith('h')
        # Nepal is UTC+5:45, so difference should be +5.75h or similar
        assert "+" in result["time_difference"]