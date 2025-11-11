#!/usr/bin/env python3
"""
Standalone test script for multi-token authentication functionality.
Tests the auth logic without importing the package.
"""

import os
import tempfile
from typing import Optional, Set


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
        print(f"Loaded {len(token_list)} tokens from API_BEARER_TOKEN")

    # Method 2: Token file (one token per line)
    token_file = os.getenv("API_BEARER_TOKENS_FILE")
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                file_tokens = [line.strip() for line in f if line.strip()]
                tokens.update(file_tokens)
                print(f"Loaded {len(file_tokens)} tokens from file: {token_file}")
        except Exception as e:
            print(f"Error reading token file {token_file}: {e}")

    # Remove empty tokens
    tokens.discard("")

    if tokens:
        print(f"Total {len(tokens)} unique tokens configured")
        return tokens
    else:
        print("No bearer tokens configured - authentication disabled")
        return None


def test_single_token():
    """Test single token configuration (backward compatibility)."""
    print("\n=== Testing single token configuration ===")

    # Set single token
    os.environ["API_BEARER_TOKEN"] = "single-token-123"
    os.environ.pop("API_BEARER_TOKENS_FILE", None)

    tokens = _parse_bearer_tokens()

    assert tokens == {"single-token-123"}, f"Expected single token, got {tokens}"
    print("✓ Single token test passed")


def test_multiple_tokens_comma_separated():
    """Test multiple tokens with comma separation."""
    print("\n=== Testing multiple tokens (comma-separated) ===")

    # Set multiple tokens
    os.environ["API_BEARER_TOKEN"] = "token1,token2,token3,token4"
    os.environ.pop("API_BEARER_TOKENS_FILE", None)

    tokens = _parse_bearer_tokens()

    expected = {"token1", "token2", "token3", "token4"}
    assert tokens == expected, f"Expected {expected}, got {tokens}"
    print("✓ Multiple tokens (comma-separated) test passed")


def test_token_file():
    """Test token file configuration."""
    print("\n=== Testing token file configuration ===")

    # Create temporary token file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("file-token-1\n")
        f.write("file-token-2\n")
        f.write("file-token-3\n")
        f.write("\n")  # Empty line should be ignored
        f.write("file-token-4\n")
        token_file = f.name

    try:
        # Set token file
        os.environ.pop("API_BEARER_TOKEN", None)
        os.environ["API_BEARER_TOKENS_FILE"] = token_file

        tokens = _parse_bearer_tokens()

        expected = {"file-token-1", "file-token-2", "file-token-3", "file-token-4"}
        assert tokens == expected, f"Expected {expected}, got {tokens}"
        print("✓ Token file test passed")

    finally:
        # Clean up
        os.unlink(token_file)


def test_combined_configuration():
    """Test combination of environment variable and file."""
    print("\n=== Testing combined configuration ===")

    # Create temporary token file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("file-token-1\n")
        f.write("file-token-2\n")
        token_file = f.name

    try:
        # Set both environment variable and file
        os.environ["API_BEARER_TOKEN"] = "env-token-1,env-token-2"
        os.environ["API_BEARER_TOKENS_FILE"] = token_file

        tokens = _parse_bearer_tokens()

        expected = {"env-token-1", "env-token-2", "file-token-1", "file-token-2"}
        assert tokens == expected, f"Expected {expected}, got {tokens}"
        print("✓ Combined configuration test passed")

    finally:
        # Clean up
        os.unlink(token_file)


def test_no_tokens():
    """Test no token configuration (authentication disabled)."""
    print("\n=== Testing no token configuration ===")

    # Clear all token configurations
    os.environ.pop("API_BEARER_TOKEN", None)
    os.environ.pop("API_BEARER_TOKENS_FILE", None)

    tokens = _parse_bearer_tokens()

    assert tokens is None, f"Expected None (no auth), got {tokens}"
    print("✓ No token test passed")


def test_whitespace_handling():
    """Test whitespace handling in tokens."""
    print("\n=== Testing whitespace handling ===")

    # Set tokens with whitespace
    os.environ["API_BEARER_TOKEN"] = " token1 , token2 ,token3, token4 "
    os.environ.pop("API_BEARER_TOKENS_FILE", None)

    tokens = _parse_bearer_tokens()

    expected = {"token1", "token2", "token3", "token4"}
    assert tokens == expected, f"Expected {expected}, got {tokens}"
    print("✓ Whitespace handling test passed")


def test_duplicate_tokens():
    """Test handling of duplicate tokens."""
    print("\n=== Testing duplicate token handling ===")

    # Create temporary token file with duplicates
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("token1\n")
        f.write("token2\n")
        token_file = f.name

    try:
        # Set environment variable with overlapping tokens
        os.environ["API_BEARER_TOKEN"] = "token1,token3"
        os.environ["API_BEARER_TOKENS_FILE"] = token_file

        tokens = _parse_bearer_tokens()

        expected = {"token1", "token2", "token3"}
        assert tokens == expected, f"Expected {expected}, got {tokens}"
        print("✓ Duplicate token handling test passed")

    finally:
        # Clean up
        os.unlink(token_file)


def main():
    """Run all tests."""
    print("Running multi-token authentication tests...")

    try:
        test_single_token()
        test_multiple_tokens_comma_separated()
        test_token_file()
        test_combined_configuration()
        test_no_tokens()
        test_whitespace_handling()
        test_duplicate_tokens()

        print("\n🎉 All tests passed! Multi-token authentication is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Clean up environment
        os.environ.pop("API_BEARER_TOKEN", None)
        os.environ.pop("API_BEARER_TOKENS_FILE", None)

    return 0


if __name__ == "__main__":
    exit(main())
