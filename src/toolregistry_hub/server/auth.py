"""Authentication and security utilities for API routes."""

import os
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Define the token authentication scheme
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer Token.

    Args:
        credentials: HTTP authorization credentials from request header

    Raises:
        HTTPException: If token is invalid or missing when required
    """
    valid_token = os.getenv("API_BEARER_TOKEN")

    # If the token is empty or not set, disable verification
    if not valid_token:
        return

    if credentials.credentials != valid_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
        )


def get_security_dependencies() -> List:
    """Get security dependencies based on environment configuration.

    Returns:
        List of security dependencies. Empty if no token is required.
    """
    token_required = bool(os.getenv("API_BEARER_TOKEN"))
    return [] if not token_required else [Depends(verify_token)]
