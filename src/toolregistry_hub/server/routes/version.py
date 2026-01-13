"""Version checking endpoints for the ToolRegistry Hub server."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...version_check import check_for_updates

router = APIRouter(prefix="/version", tags=["version"])


@router.get("/", include_in_schema=False)
async def get_version_info():
    """Get current version information and check for updates.

    Returns:
        JSON response containing version information, update status,
        and installation instructions if an update is available.
    """
    version_info = await check_for_updates()

    return JSONResponse(content=version_info, status_code=200)


@router.get("/check", include_in_schema=False)
async def check_updates():
    """Check for available updates.

    Returns:
        JSON response with update availability information.
    """
    version_info = await check_for_updates()

    # Return a simplified response focused on update status
    response = {
        "update_available": version_info["update_available"],
        "current_version": version_info["current_version"],
        "latest_version": version_info["latest_version"],
        "message": version_info["message"],
    }

    if version_info["update_available"]:
        response["install_command"] = version_info["install_command"]
        response["pypi_url"] = version_info["pypi_url"]

    return JSONResponse(content=response, status_code=200)
