"""Authentication and security utilities for API routes."""

import os
from typing import Optional, Set

from loguru import logger

from ..utils.api_key_parser import APIKeyParser


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

    if "API_BEARER_TOKEN" in os.environ:
        # Use APIKeyParser to parse and validate tokens
        try:
            parser = APIKeyParser(env_var_name="API_BEARER_TOKEN")
            token_list = list(parser.api_keys)
            tokens.update(token_list)
            logger.info(f"Loaded {len(token_list)} tokens from API_BEARER_TOKEN")
        except ValueError as e:
            logger.warning(f"Failed to parse API_BEARER_TOKEN: {e}")

    # Method 2: Token file (one token per line)
    token_file = os.getenv("API_BEARER_TOKENS_FILE")
    if token_file:
        try:
            # Use APIKeyParser with file support
            parser = APIKeyParser(api_tokens_file=token_file)
            valid_file_tokens = list(parser.api_keys)
            tokens.update(valid_file_tokens)
            logger.info(
                f"Loaded {len(valid_file_tokens)} tokens from env: API_BEARER_TOKENS_FILE={token_file}"
            )
        except ValueError as e:
            logger.error(f"Error reading token file {token_file}: {e}")

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
