"""Unit Converter API routes."""

import json
import textwrap
from typing import Any, Dict, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...unit_converter import UnitConverter

# ============================================================
# Request models
# ============================================================


class UnitConvertRequest(BaseModel):
    """Request model for unit conversion."""

    value: float = Field(
        description="Value to convert",
        examples=[100],
    )
    conversion: str = Field(
        description="Name of the conversion function to use",
        examples=["celsius_to_fahrenheit"],
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional keyword arguments for the conversion function",
        examples=[{"area": 2}],
    )


class UnitListConversionsRequest(BaseModel):
    """Request model for listing available conversions."""

    category: Literal[
        "all",
        "temperature",
        "length",
        "weight",
        "time",
        "capacity",
        "area",
        "speed",
        "data_storage",
        "pressure",
        "power",
        "energy",
        "frequency",
        "fuel_economy",
        "electrical",
        "magnetic",
        "radiation",
        "light_intensity",
    ] = Field(
        default="all",
        description="Category of conversions to list",
    )
    with_help: bool = Field(
        default=False,
        description="Include help messages for each conversion function",
    )


class UnitHelpRequest(BaseModel):
    """Request model for unit converter help."""

    fn_name: str = Field(
        description="Conversion function name to get help for",
        examples=["celsius_to_fahrenheit"],
    )


# ============================================================
# Response models
# ============================================================


class UnitHelpResponse(BaseModel):
    """Response model for unit converter help."""

    help_text: str = Field(
        ..., description="Help text for the specified conversion function"
    )


class UnitListConversionsResponse(BaseModel):
    """Response model for listing available conversions."""

    conversions: Dict[str, str] = Field(
        ...,
        description="Dictionary of conversion functions with optional help messages",
    )


class UnitConvertResponse(BaseModel):
    """Response model for unit conversion."""

    result: float = Field(..., description="Result of the unit conversion")


# ============================================================
# API routes
# ============================================================

# Initialize unit converter instance
unit_converter = UnitConverter()

# Create router with prefix and tags
router = APIRouter(prefix="/unit", tags=["unit_converter"])


@router.post(
    "/help",
    summary="Get help with particular conversion function",
    description=unit_converter.help.__doc__,
    operation_id="unit-help",
    response_model=UnitHelpResponse,
)
def unit_help(data: UnitHelpRequest) -> UnitHelpResponse:
    """Get help with unit conversion functions.

    Args:
        data: Request containing conversion function name to get help for

    Returns:
        Response containing help text for the specified function

    Raises:
        HTTPException: If function name is invalid
    """
    try:
        help_text = unit_converter.help(data.fn_name)
        return UnitHelpResponse(help_text=help_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid function name: {str(e)}",
        ) from e


@router.post(
    "/list_conversions",
    summary="Get available conversion functions",
    description=unit_converter.list_conversions.__doc__,
    operation_id="unit-list_conversions",
    response_model=UnitListConversionsResponse,
)
def unit_list_conversions(
    data: UnitListConversionsRequest,
) -> UnitListConversionsResponse:
    """Get available conversion functions.

    Args:
        data: Request containing category and whether to include help messages

    Returns:
        Response containing dictionary of conversion functions with optional help messages
    """
    conversions_data = json.loads(
        unit_converter.list_conversions(data.category, data.with_help)
    )
    if isinstance(conversions_data, list):
        conversions = {fn: "" for fn in conversions_data}
    else:
        conversions = conversions_data
    return UnitListConversionsResponse(conversions=conversions)


@router.post(
    "/convert",
    summary="Perform a unit conversion",
    description=textwrap.dedent(
        """Performs a unit conversion using the specified conversion function.

        This is a convenience method that allows calling any conversion function by name.

        - Use `unit-list_conversions` to view available conversion functions. Set `with_help` to `True` to include function signatures and docstrings.
        - Use `unit-help` for detailed information on specific conversion functions.

        **Note**: Some conversion functions require additional parameters (e.g., `area` for lux/lumen conversions). Pass these in the `kwargs` field.
        """
    ),
    operation_id="unit-convert",
    response_model=UnitConvertResponse,
)
def unit_convert(data: UnitConvertRequest) -> UnitConvertResponse:
    """Perform a unit conversion.

    Args:
        data: Request containing value, conversion function name, and optional kwargs

    Returns:
        Response containing result of the unit conversion

    Raises:
        HTTPException: If conversion function is invalid or required parameters are missing
    """
    try:
        result = unit_converter.convert(data.value, data.conversion, **data.kwargs)
        return UnitConvertResponse(result=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversion failed: {str(e)}",
        ) from e
