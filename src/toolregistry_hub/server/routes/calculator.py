"""Calculator API routes."""

import json
import textwrap
from typing import Dict, Union

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...calculator import Calculator

# ============================================================
# Request models
# ============================================================


class CalcEvaluateRequest(BaseModel):
    """Request model for calculator evaluation."""

    expression: str = Field(
        description="Mathematical expression to evaluate",
        examples=["26 * 9 / 5 + 32"],
    )


class CalcListAllowedFnsRequest(BaseModel):
    """Request model for listing allowed calculator functions."""

    with_help: bool = Field(
        False, description="Include help messages for each function"
    )


class CalcHelpRequest(BaseModel):
    """Request model for calculator help."""

    fn_name: str = Field(description="Function name to get help for", examples=["sin"])


# ============================================================
# Response models
# ============================================================


class CalcHelpResponse(BaseModel):
    """Response model for calculator help."""

    help_text: str = Field(..., description="Help text for the specified function")


class CalcListAllowedFnsResponse(BaseModel):
    """Response model for listing allowed calculator functions."""

    functions: Dict[str, str] = Field(
        ..., description="Dictionary of allowed functions with optional help messages"
    )


class CalcEvaluateResponse(BaseModel):
    """Response model for calculator evaluation."""

    result: Union[float, int, bool] = Field(
        ..., description="Result of the mathematical expression"
    )


# ============================================================
# API routes
# ============================================================

# Initialize calculator instance
calculator = Calculator()

# Create router with prefix and tags
router = APIRouter(prefix="/calc", tags=["calculator"])


@router.post(
    "/help",
    summary="Get help with particular calculator function",
    description=calculator.help.__doc__,
    operation_id="calc-help",
    response_model=CalcHelpResponse,
)
def calc_help(data: CalcHelpRequest) -> CalcHelpResponse:
    """Get help with calculator functions.

    Args:
        data: Request containing function name to get help for

    Returns:
        Response containing help text for the specified function

    Raises:
        HTTPException: If function name is invalid
    """
    try:
        help_text = calculator.help(data.fn_name)
        return CalcHelpResponse(help_text=help_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid function name: {str(e)}",
        ) from e


@router.post(
    "/allowed_fns",
    summary="Get allowed functions for `evaluate`",
    description=calculator.list_allowed_fns.__doc__,
    operation_id="calc-list_allowed_fns",
    response_model=CalcListAllowedFnsResponse,
)
def calc_list_allowed_fns(
    data: CalcListAllowedFnsRequest,
) -> CalcListAllowedFnsResponse:
    """Get allowed functions for calculator.

    Args:
        data: Request containing whether to include help messages

    Returns:
        Response containing dictionary of allowed functions with optional help messages
    """
    allowed = json.loads(calculator.list_allowed_fns(data.with_help))
    if isinstance(allowed, list):
        functions = {fn: "" for fn in allowed}
    else:
        functions = allowed
    return CalcListAllowedFnsResponse(functions=functions)


@router.post(
    "/evaluate",
    summary="Evaluate a mathematical expression",
    description=textwrap.dedent(
        """Evaluates a mathematical expression.

        The `expression` can use named functions like `add(2, 3)` or native operators like `2 + 3`. Pay attention to operator precedence and use parentheses to ensure the intended order of operations. For example: `"add(2, 3) * pow(2, 3) + sqrt(16)"` or `"(2 + 3) * (2 ** 3) + sqrt(16)"` or mixed.

        - Use `calc-list_allowed_fns()` to view available functions. Set `with_help` to `True` to include function signatures and docstrings.
        - Use `calc-help` for detailed information on specific functions.

        **Note**: If an error occurs due to an invalid expression, query the `help` method to check the function usage and ensure it is listed by `calc-list_allowed_fns()`.
        """
    ),
    operation_id="calc-evaluate",
    response_model=CalcEvaluateResponse,
)
def calc_evaluate(data: CalcEvaluateRequest) -> CalcEvaluateResponse:
    """Evaluate a mathematical expression.

    Args:
        data: Request containing the expression to evaluate

    Returns:
        Response containing result of the mathematical expression

    Raises:
        HTTPException: If expression is empty or invalid
    """
    expression = data.expression.strip()  # Remove leading/trailing whitespace
    if not expression:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expression cannot be empty.",
        )
    try:
        result = calculator.evaluate(expression)
        return CalcEvaluateResponse(result=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid expression: {str(e)}",
        ) from e
