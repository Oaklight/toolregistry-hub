"""Authentication and security utilities for API routes."""

import os
from typing import Optional, Set

from fastapi.security import HTTPBearer
from loguru import logger

# Define the token authentication scheme
security = HTTPBearer()


def _parse_bearer_tokens() -> Optional[Set[str]]:
    """Parse bearer tokens from environment variables.

    Supports two configuration formats:
    1. API_BEARER_TOKEN: single token or comma-separated multiple tokens
    2. API_BEARER_TOKENS_FILE: file path with one token per line

    Returns:
        Set of valid tokens, or None if no tokens configured
    """
    tokens = set()

    # Method 1: Environment variable (single or comma-separated)
    env_tokens = os.getenv("API_BEARER_TOKEN")
    if env_tokens:
        env_tokens = env_tokens.strip()
        # Split by comma and clean up
        token_list = [token.strip() for token in env_tokens.split(",") if token.strip()]
        tokens.update(token_list)
        logger.info(f"Loaded {len(token_list)} tokens from API_BEARER_TOKEN")

    # Method 2: Token file (one token per line)
    token_file = os.getenv("API_BEARER_TOKENS_FILE")
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                file_tokens = [line.strip() for line in f if line.strip()]
                tokens.update(file_tokens)
                logger.info(f"Loaded {len(file_tokens)} tokens from file: {token_file}")
        except Exception as e:
            logger.error(f"Error reading token file {token_file}: {e}")

    # Remove empty tokens
    tokens.discard("")

    if tokens:
        logger.info(f"Total {len(tokens)} unique tokens configured")
        return tokens
    else:
        logger.info("No bearer tokens configured - authentication disabled")
        return None


# Cache parsed tokens to avoid repeated parsing
_cached_tokens: Optional[Set[str]] = None


def get_valid_tokens() -> Optional[Set[str]]:
    """Get cached valid tokens."""
    global _cached_tokens
    if _cached_tokens is None:
        _cached_tokens = _parse_bearer_tokens()
    return _cached_tokens
