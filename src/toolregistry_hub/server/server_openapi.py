"""FastAPI server implementation with global dependencies authentication.

This module provides a FastAPI application using global dependencies
for token authentication, following FastAPI best practices.
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from .auth import get_valid_tokens
from .server_core import create_core_app

# Define the token authentication scheme
security = HTTPBearer()


async def verify_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """Verify Bearer token from Authorization header.

    Args:
        credentials: HTTP Bearer credentials from the Authorization header

    Returns:
        The verified token string

    Raises:
        HTTPException: If token is invalid or missing when required
    """
    valid_tokens = get_valid_tokens()

    # If no tokens configured, disable verification
    if not valid_tokens:
        return ""

    # Extract token from credentials
    token = credentials.credentials

    if token not in valid_tokens:
        logger.warning(f"Invalid token attempt: {token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Authenticated request with token: {token[:8]}...")
    return token


def create_fastapi_app() -> FastAPI:
    """Create FastAPI application with global dependencies authentication.

    This implementation uses FastAPI's global dependencies feature to apply
    authentication to all routes automatically, following the pattern shown
    in the FastAPI documentation.

    Returns:
        FastAPI application with global dependencies authentication
    """
    # Create the core app instance

    # Determine if authentication is needed
    valid_tokens = get_valid_tokens()
    dependencies = []

    if valid_tokens:
        # Add global authentication dependency
        dependencies.append(Depends(verify_bearer_token))
        logger.info(
            "Token authentication enabled for FastAPI server (global dependencies)"
        )
    else:
        logger.info(
            "No tokens configured - FastAPI server running without authentication"
        )
    app = create_core_app(dependencies=dependencies)

    # # Override the core app with global dependencies

    # core_app.title = "ToolRegistry-Hub FastAPI Server"
    # core_app.description = "A FastAPI server for accessing various tools like calculators, unit converters, and web search engines with global dependencies authentication."
    # core_app.dependencies.extend(dependencies)

    logger.info("FastAPI app initialized with global dependencies authentication")
    return app


# Create the default FastAPI app instance
app = create_fastapi_app()
