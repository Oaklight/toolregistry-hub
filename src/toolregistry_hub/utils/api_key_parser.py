"""API Key Parser Utility

This module provides a generic API key parser that can handle multiple API keys
with round-robin selection and validation. It's designed to be used across
different web search implementations.
"""

import os
import re
import time
from typing import Dict, List, Optional


class APIKeyParser:
    """Generic API key parser for handling multiple API keys with round-robin selection."""

    def __init__(
        self,
        api_keys: Optional[str] = None,
        env_var_name: Optional[str] = None,
        api_tokens_file: Optional[str] = None,
        key_separator: str = ",",
        rate_limit_delay: float = 1.0,
    ):
        """Initialize API key parser.

        Args:
            api_keys: Comma-separated API keys string. If not provided, will try to get from env_var_name.
            env_var_name: Environment variable name to get API keys from.
            api_tokens_file: Path to file containing API keys (one per line). If provided, will try to read from this file.
            key_separator: Separator used to split multiple API keys. Defaults to ",".
            rate_limit_delay: Delay between requests in seconds to avoid rate limits.

        Raises:
            ValueError: If no valid API keys are provided or found in environment.
        """
        # Try to get API keys from parameter, environment variable, or file
        api_keys_str = api_keys or (env_var_name and os.getenv(env_var_name))

        # If no keys found yet and file path is provided, try to read from file
        if not api_keys_str and api_tokens_file:
            api_keys_str = self._read_keys_from_file(api_tokens_file)

        if not api_keys_str:
            raise ValueError(
                f"API keys are required. Set {env_var_name} environment variable, "
                "pass api_keys parameter (comma-separated), or provide api_tokens_file."
            )

        # Parse and validate API keys
        self.api_keys = self._parse_api_keys(api_keys_str, key_separator)
        if not self.api_keys:
            raise ValueError("No valid API keys provided")

        self._current_key_index = 0
        self.rate_limit_delay = rate_limit_delay
        # Track last request time for each API key individually
        self._last_request_times: Dict[str, float] = {}

    def _parse_api_keys(self, api_keys_str: str, separator: str) -> List[str]:
        """Parse and validate API keys from string.

        Args:
            api_keys_str: String containing comma-separated API keys
            separator: Separator used to split the keys

        Returns:
            List of valid API keys
        """
        # Split by separator and strip whitespace
        keys = [key.strip() for key in api_keys_str.split(separator) if key.strip()]

        # Filter out empty or invalid keys
        valid_keys = []
        for key in keys:
            # Basic validation: check if key looks like a valid API key
            if self._is_valid_api_key(key):
                valid_keys.append(key)
            else:
                # Log warning for invalid keys but continue processing
                import logging

                logging.warning(f"Skipping invalid API key: {key[:10]}...")

        return valid_keys

    def _is_valid_api_key(self, key: str) -> bool:
        """Basic validation for API key format.

        This is a simple check to filter out obviously invalid keys.
        Override this method for more specific validation.

        Args:
            key: API key string to validate

        Returns:
            True if key appears valid, False otherwise
        """
        # # Check minimum length (most API keys are at least 10 characters)
        # if len(key) < 10:
        #     return False

        # # Check for common API key patterns
        # # This is a basic check - you can extend this for specific providers
        # patterns = [
        #     r"^[a-zA-Z0-9_-]+$",  # Alphanumeric with underscores and dashes
        #     r"^[a-fA-F0-9-]+$",  # UUID-like format
        #     r"^sk-[a-zA-Z0-9]+$",  # OpenAI-like format
        #     r"^AIza[0-9A-Za-z-_]{35}$",  # Google API key format
        # ]

        # for pattern in patterns:
        #     if re.match(pattern, key):
        #         return True

        # key can't contain whitespace
        if len(key.split()) > 1:
            return False

        # If no specific pattern matches, accept it as long as it's not empty
        return len(key) > 0

    def _read_keys_from_file(self, file_path: str) -> str:
        """Read API keys from a file (one key per line).

        Args:
            file_path: Path to the file containing API keys

        Returns:
            String containing comma-separated API keys

        Raises:
            ValueError: If file cannot be read or is empty
        """
        try:
            if not os.path.exists(file_path):
                raise ValueError(f"API tokens file not found: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                file_tokens = [line.strip() for line in f if line.strip()]

            if not file_tokens:
                raise ValueError(f"No API keys found in file: {file_path}")

            # Join with comma separator for parsing
            return ",".join(file_tokens)

        except Exception as e:
            import logging

            logging.error(f"Error reading API tokens from file {file_path}: {e}")
            raise ValueError(f"Failed to read API tokens from file: {e}")

    def get_next_api_key(self) -> str:
        """Get the next API key using round-robin selection.

        Returns:
            The next API key in the rotation
        """
        if not self.api_keys:
            raise ValueError("No API keys available")

        key = self.api_keys[self._current_key_index]
        self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
        return key

    @property
    def key_count(self) -> int:
        """Get the number of valid API keys."""
        return len(self.api_keys)

    def get_key_info(self) -> dict:
        """Get information about the API keys.

        Returns:
            Dictionary with key count and current index
        """
        return {
            "key_count": self.key_count,
            "current_index": self._current_key_index,
        }

    def __len__(self) -> int:
        """Return the number of API keys."""
        return self.key_count

    def __getitem__(self, index: int) -> str:
        """Get API key by index."""
        if 0 <= index < len(self.api_keys):
            return self.api_keys[index]
        raise IndexError(f"Index {index} out of range for {len(self.api_keys)} keys")

    def wait_for_rate_limit(self, api_key: Optional[str] = None):
        """Ensure minimum delay between API requests to avoid rate limits for a specific key.

        Args:
            api_key: The API key to check rate limit for. If None, uses the last used key.
        """
        if api_key is None:
            # Use the last used key (the one that was just selected)
            if self._current_key_index == 0:
                # If we're at the beginning, use the last key
                api_key = self.api_keys[-1]
            else:
                api_key = self.api_keys[self._current_key_index - 1]

        current_time = time.time()

        # Get the last request time for this specific API key
        last_request_time = self._last_request_times.get(api_key, 0)
        time_since_last_request = current_time - last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            import logging

            logging.debug(
                f"Rate limiting for key {api_key[:10]}...: sleeping for {sleep_time:.2f}s"
            )
            time.sleep(sleep_time)

        # Update the last request time for this specific API key
        self._last_request_times[api_key] = time.time()


def create_api_key_parser(
    api_keys: Optional[str] = None,
    env_var_name: Optional[str] = None,
    api_tokens_file: Optional[str] = None,
    key_separator: str = ",",
    rate_limit_delay: float = 1.0,
) -> APIKeyParser:
    """Factory function to create an API key parser.

    Args:
        api_keys: Comma-separated API keys string
        env_var_name: Environment variable name to get API keys from
        api_tokens_file: Path to file containing API keys (one per line)
        key_separator: Separator used to split multiple API keys
        rate_limit_delay: Delay between requests in seconds to avoid rate limits

    Returns:
        Configured APIKeyParser instance

    Example:
        >>> # Using environment variable
        >>> parser = create_api_key_parser(env_var_name="MY_API_KEYS")
        >>>
        >>> # Using direct keys
        >>> parser = create_api_key_parser(api_keys="key1,key2,key3")
        >>>
        >>> # Using file with API keys
        >>> parser = create_api_key_parser(api_tokens_file="/path/to/keys.txt")
        >>>
        >>> # Using custom separator and rate limit
        >>> parser = create_api_key_parser(
        ...     env_var_name="MY_API_KEYS",
        ...     key_separator=";",
        ...     rate_limit_delay=2.0
        ... )
    """
    return APIKeyParser(
        api_keys=api_keys,
        env_var_name=env_var_name,
        api_tokens_file=api_tokens_file,
        key_separator=key_separator,
        rate_limit_delay=rate_limit_delay,
    )
