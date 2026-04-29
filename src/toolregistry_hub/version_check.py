"""Version checking utilities for PyPI updates.

This module provides functionality to check for available updates
on PyPI and compare versions.
"""

from ._vendor.httpclient import AsyncClient

from . import __version__
from ._vendor.structlog import get_logger

logger = get_logger()


async def get_latest_pypi_version(
    package_name: str = "toolregistry-hub",
) -> str | None:
    """Get the latest version of a package from PyPI.

    Args:
        package_name: Name of the package to check on PyPI

    Returns:
        Latest version string if successful, None if failed
    """
    try:
        async with AsyncClient() as client:
            response = await client.get(
                f"https://pypi.org/pypi/{package_name}/json",
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
                timeout=5.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["info"]["version"]
    except Exception as e:
        logger.debug(f"Failed to fetch latest version from PyPI: {e}")
        return None


def _pre_release_weight(pre_release_part: str) -> int:
    """Map a pre-release suffix to a sort weight.

    Args:
        pre_release_part: The non-numeric suffix, e.g. ``"a1"``, ``"rc2"``.

    Returns:
        Negative integer (alpha < beta < rc < other < release).
    """
    if "a" in pre_release_part:
        return -3
    if "b" in pre_release_part:
        return -2
    if "rc" in pre_release_part:
        return -1
    return -4


def _parse_version_tuple(v: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple of integers.

    Handles standard versions (``"1.2.3"``) and pre-release tags
    (``"1.0.0a1"``, ``"2.0.0rc1"``).

    Args:
        v: Version string.

    Returns:
        Tuple of integers suitable for comparison.
    """
    parts: list[int] = []
    weight = 0

    for segment in v.split("."):
        numeric = ""
        for i, char in enumerate(segment):
            if char.isdigit():
                numeric += char
            else:
                pre = segment[i:]
                weight = _pre_release_weight(pre)
                break

        parts.append(int(numeric) if numeric else 0)

    parts.append(weight)
    return tuple(parts)


def compare_versions(current: str, latest: str) -> bool:
    """Compare two version strings to determine if an update is available.

    Args:
        current: Current version string
        latest: Latest version string

    Returns:
        True if latest > current, False otherwise
    """
    try:
        return _parse_version_tuple(latest) > _parse_version_tuple(current)
    except Exception as e:
        logger.debug(f"Version comparison failed: {e}")
        return False


async def check_for_updates(package_name: str = "toolregistry-hub") -> dict:
    """Check for available updates and return comprehensive version information.

    Args:
        package_name: Name of the package to check

    Returns:
        Dictionary containing version information and update status
    """
    current_version = __version__
    latest_version = await get_latest_pypi_version(package_name)

    result = {
        "current_version": current_version,
        "latest_version": latest_version,
        "update_available": False,
        "pypi_url": f"https://pypi.org/project/{package_name}/",
        "install_command": f"pip install --upgrade {package_name}",
    }

    if latest_version:
        result["update_available"] = compare_versions(current_version, latest_version)

        if result["update_available"]:
            result["message"] = f"New version {latest_version} available"
        else:
            result["message"] = "You're using the latest version"
    else:
        result["message"] = "Unable to check for updates"

    return result


def get_version_check_sync(package_name: str = "toolregistry-hub") -> str:
    """Synchronous version check for CLI usage.

    Args:
        package_name: Name of the package to check

    Returns:
        Formatted version string with update information
    """
    import asyncio

    try:
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, just return the current version
            logger.debug("Already in event loop, skipping async version check")
            return __version__
        except RuntimeError:
            # No running loop, safe to create a new one
            pass

        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(check_for_updates(package_name))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    except Exception as e:
        logger.debug(f"Sync version check failed: {e}")
        return __version__

    version_lines = [__version__]

    if result["latest_version"] and result["update_available"]:
        version_lines.extend(
            [
                f"New version available: {result['latest_version']}",
                f"Update with `{result['install_command']}`",
            ]
        )

    return "\n".join(version_lines)
