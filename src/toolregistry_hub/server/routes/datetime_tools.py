"""DateTime API routes."""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ...datetime_utils import DateTime

# ============================================================
# Request models
# ============================================================


class TimeNowRequest(BaseModel):
    """Request model for getting current time."""

    timezone_name: Optional[str] = Field(
        None,
        description="Optional timezone name (e.g., 'Asia/Shanghai', 'UTC+5'). Defaults to UTC if not specified.",
        examples=["Asia/Shanghai", "UTC+8", "America/New_York"],
    )


class ConvertTimezoneRequest(BaseModel):
    """Request model for timezone conversion."""

    time_str: str = Field(
        description="Time in 24-hour format (HH:MM)",
        examples=["14:30"],
    )
    source_timezone: str = Field(
        description="Source timezone (e.g., 'America/Chicago', 'UTC+5')",
        examples=["America/New_York"],
    )
    target_timezone: str = Field(
        description="Target timezone (e.g., 'Asia/Shanghai', 'GMT-3')",
        examples=["Asia/Shanghai"],
    )


# ============================================================
# Response models
# ============================================================


class TimeNowResponse(BaseModel):
    """Response model for current time."""

    current_time: str = Field(..., description="Current time in ISO 8601 format")
    timezone: Optional[str] = Field(None, description="Timezone used (if specified)")


class ConvertTimezoneResponse(BaseModel):
    """Response model for timezone conversion."""

    source_time: str = Field(..., description="Source time in ISO 8601 format")
    target_time: str = Field(..., description="Target time in ISO 8601 format")
    time_difference: str = Field(..., description="Time difference between timezones")
    source_timezone: str = Field(..., description="Source timezone")
    target_timezone: str = Field(..., description="Target timezone")


# ============================================================
# API routes
# ============================================================

# Create router with prefix and tags
router = APIRouter(prefix="/time", tags=["datetime"])


@router.post(
    "/now",
    summary="Get current time in ISO 8601 format",
    description="Get current time in ISO 8601 format. Optionally specify a timezone, otherwise returns UTC time.",
    operation_id="time-now",
    response_model=TimeNowResponse,
)
def time_now(request: TimeNowRequest) -> TimeNowResponse:
    """Get current time in ISO 8601 format.

    Args:
        request: Request containing optional timezone name. Supports both IANA timezone names
                (e.g., "America/New_York") and UTC/GMT offset formats
                (e.g., "UTC+5", "GMT-3", "UTC+5:30"). Defaults to UTC if None.

    Returns:
        Response containing current time as ISO 8601 formatted string

    Raises:
        HTTPException: If timezone format is invalid
    """
    try:
        current_time = DateTime.now(request.timezone_name)
        return TimeNowResponse(
            current_time=current_time, timezone=request.timezone_name
        )
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/convert",
    summary="Convert time between timezones",
    description="Convert a specific time from one timezone to another. Supports both IANA timezone names and UTC/GMT offset formats.",
    operation_id="time-convert-timezone",
    response_model=ConvertTimezoneResponse,
)
def convert_timezone(request: ConvertTimezoneRequest) -> ConvertTimezoneResponse:
    """Convert time between timezones.

    Args:
        request: Request containing time string and source/target timezones

    Returns:
        Response containing converted time information

    Raises:
        HTTPException: If timezone or time format is invalid
    """
    try:
        result = DateTime.convert_timezone(
            request.time_str, request.source_timezone, request.target_timezone
        )
        return ConvertTimezoneResponse(**result)
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(e))
