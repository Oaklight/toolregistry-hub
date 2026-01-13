"""Tests for version checking functionality."""

import pytest
from unittest.mock import patch, MagicMock

from toolregistry_hub.version_check import (
    compare_versions,
    get_version_check_sync,
)


class TestCompareVersions:
    """Test version comparison functionality."""

    def test_basic_version_comparison(self):
        """Test basic version number comparisons."""
        # Test newer version
        assert compare_versions("1.0.0", "1.0.1") is True
        assert compare_versions("1.0.0", "1.1.0") is True
        assert compare_versions("1.0.0", "2.0.0") is True
        
        # Test older version
        assert compare_versions("1.0.1", "1.0.0") is False
        assert compare_versions("1.1.0", "1.0.0") is False
        assert compare_versions("2.0.0", "1.0.0") is False
        
        # Test same version
        assert compare_versions("1.0.0", "1.0.0") is False

    def test_prerelease_version_comparison(self):
        """Test pre-release version comparisons."""
        # Pre-release vs stable
        assert compare_versions("1.0.0a1", "1.0.0") is True
        assert compare_versions("1.0.0b1", "1.0.0") is True
        assert compare_versions("1.0.0rc1", "1.0.0") is True
        
        # Pre-release ordering
        assert compare_versions("1.0.0a1", "1.0.0b1") is True
        assert compare_versions("1.0.0b1", "1.0.0rc1") is True
        assert compare_versions("1.0.0a1", "1.0.0rc1") is True

    def test_complex_version_comparison(self):
        """Test complex version scenarios."""
        assert compare_versions("0.5.3", "0.6.0") is True
        assert compare_versions("2.1.0", "2.0.9") is False
        assert compare_versions("1.0.0", "1.0.0.1") is True

    def test_version_comparison_error_handling(self):
        """Test error handling in version comparison."""
        # Should not crash on invalid versions, but may return unexpected results
        # The current implementation tries to parse what it can
        result1 = compare_versions("invalid", "1.0.0")
        result2 = compare_versions("1.0.0", "invalid")
        result3 = compare_versions("", "")
        
        # These should not crash, results may vary based on implementation
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)
        assert isinstance(result3, bool)

    def test_version_comparison_edge_cases(self):
        """Test edge cases in version comparison."""
        # Test with different number of version parts
        assert compare_versions("1.0", "1.0.1") is True
        assert compare_versions("1.0.0", "1.0") is False
        
        # Test with leading zeros - our implementation treats "01" as 1
        # so "1.0.01" is treated as "1.0.1" which is > "1.0.0"
        assert compare_versions("1.0.0", "1.0.01") is True
        assert compare_versions("1.00.0", "1.0.1") is True


class TestGetVersionCheckSync:
    """Test synchronous version checking functionality."""

    def test_sync_version_check_no_loop(self):
        """Test sync version check when no event loop is running."""
        mock_result = {
            "latest_version": "1.1.0",
            "update_available": True,
            "install_command": "pip install --upgrade test-package"
        }
        
        with patch("toolregistry_hub.version_check.__version__", "1.0.0"):
            with patch("asyncio.get_running_loop", side_effect=RuntimeError("No running loop")):
                with patch("asyncio.new_event_loop") as mock_new_loop:
                    with patch("asyncio.set_event_loop"):
                        mock_loop = MagicMock()
                        mock_new_loop.return_value = mock_loop
                        mock_loop.run_until_complete.return_value = mock_result
                        
                        result = get_version_check_sync("test-package")
                        
                        expected = "1.0.0\nNew version available: 1.1.0\nUpdate with `pip install --upgrade test-package`"
                        assert result == expected

    def test_sync_version_check_with_running_loop(self):
        """Test sync version check when event loop is already running."""
        mock_loop = MagicMock()
        
        with patch("toolregistry_hub.version_check.__version__", "1.0.0"):
            with patch("asyncio.get_running_loop", return_value=mock_loop):
                result = get_version_check_sync("test-package")
                assert result == "1.0.0"

    def test_sync_version_check_error_handling(self):
        """Test sync version check error handling."""
        with patch("toolregistry_hub.version_check.__version__", "1.0.0"):
            with patch("asyncio.get_running_loop", side_effect=RuntimeError("No running loop")):
                with patch("asyncio.new_event_loop", side_effect=Exception("Loop creation failed")):
                    result = get_version_check_sync("test-package")
                    assert result == "1.0.0"


class TestVersionCheckIntegration:
    """Integration tests for version checking."""

    def test_version_comparison_comprehensive(self):
        """Comprehensive test of version comparison logic."""
        test_cases = [
            # Basic comparisons
            ("1.0.0", "1.0.1", True),
            ("1.0.1", "1.0.0", False),
            ("1.0.0", "1.0.0", False),
            
            # Major/minor version changes
            ("1.0.0", "1.1.0", True),
            ("1.0.0", "2.0.0", True),
            ("2.0.0", "1.9.9", False),
            
            # Pre-release versions
            ("1.0.0a1", "1.0.0", True),
            ("1.0.0b1", "1.0.0", True),
            ("1.0.0rc1", "1.0.0", True),
            ("1.0.0a1", "1.0.0b1", True),
            ("1.0.0b1", "1.0.0rc1", True),
            
            # Different version part counts
            ("1.0", "1.0.1", True),
            ("1.0.0", "1.0", False),
            
            # Real-world examples
            ("0.5.3", "0.6.0", True),
            ("2.1.0", "2.0.9", False),
        ]
        
        for current, latest, expected in test_cases:
            result = compare_versions(current, latest)
            assert result == expected, f"Failed: compare_versions('{current}', '{latest}') expected {expected}, got {result}"

    def test_mock_update_check(self):
        """Test update checking with mocked PyPI response."""
        with patch("toolregistry_hub.version_check.__version__", "1.0.0"):
            # Test when update is available
            with patch("asyncio.get_running_loop", side_effect=RuntimeError("No running loop")):
                with patch("asyncio.new_event_loop") as mock_new_loop:
                    with patch("asyncio.set_event_loop"):
                        mock_loop = MagicMock()
                        mock_new_loop.return_value = mock_loop
                        mock_loop.run_until_complete.return_value = {
                            "latest_version": "1.1.0",
                            "update_available": True,
                            "install_command": "pip install --upgrade toolregistry-hub"
                        }
                        
                        result = get_version_check_sync()
                        assert "1.0.0" in result
                        assert "1.1.0" in result
                        assert "pip install --upgrade toolregistry-hub" in result


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__])