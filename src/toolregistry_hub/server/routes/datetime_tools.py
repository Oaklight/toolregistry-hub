"""DateTime API routes."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...datetime_utils import DateTime
from ..auth import get_security_dependencies

# ============================================================
# Response models
# ============================================================


class TimeNowResponse(BaseModel):
    """Response model for current time."""

    current_time: str = Field(..., description="Current UTC time in ISO 8601 format")


# ============================================================
# API routes
# ============================================================

# Create router with prefix and tags
router = APIRouter(prefix="/time", tags=["datetime"])

# Get security dependencies
security_deps = get_security_dependencies()


@router.post(
    "/now",
    summary="Get current UTC time in ISO 8601 format",
    description="Get current UTC time in ISO 8601 format, useful for time-sensitive operations",
    dependencies=security_deps,
    operation_id="time-now",
    response_model=TimeNowResponse,
)
def time_now() -> TimeNowResponse:
    """Get current UTC time in ISO 8601 format.

    Returns:
        Response containing current UTC time as ISO 8601 formatted string
    """
    current_time = DateTime.now()
    return TimeNowResponse(current_time=current_time)
