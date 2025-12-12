"""
Efficient file reading with streaming and truncation.

Provides functions for reading files with line‑numbering, word‑based truncation,
and low‑memory streaming for large files.
"""

from typing import Any, Dict, Optional, Tuple

from .filesystem import validate_path


def read_file_with_limit(
    path: str,
    max_words: int = 200_000,
    max_bytes: Optional[int] = None,
    encoding: str = "utf-8",
    numbered: bool = False,
) -> Tuple[bool, str, str]:
    """Read a file with word‑based truncation using streaming.

    Args:
        path: File path.
        max_words: Maximum number of words to read (default 200k).
        max_bytes: Optional maximum bytes to read (overrides word limit).
        encoding: File encoding (default utf‑8).
        numbered: Whether to prepend line numbers.

    Returns:
        Tuple of (success, notice, content).
        success: True if file read without errors.
        notice: Informational message (e.g., truncation notice, error).
        content: Numbered lines of the read content (empty on failure).
    """
    validation = validate_path(path, require_file=True)
    if not validation["valid"]:
        return False, str(validation["message"]), ""

    try:
        # Determine byte limit (if any)
        byte_limit = max_bytes
        if byte_limit is None:
            # No byte limit, but we still need to stop after enough words
            byte_limit = 0  # 0 means unlimited

        with open(path, "r", encoding=encoding, errors="replace") as f:
            if byte_limit > 0:
                # Read up to byte_limit bytes, then decode
                raw = f.read(byte_limit)
                if f.read(1):  # check if more data exists
                    truncated = True
                else:
                    truncated = False
            else:
                # Stream reading with word counting
                lines = []
                word_count = 0
                truncated = False
                for line in f:
                    lines.append(line)
                    # Simple word count (split by whitespace)
                    word_count += len(line.split())
                    if word_count >= max_words:
                        truncated = True
                        break
                raw = "".join(lines)

        # If we didn't stream by words, we need to apply word truncation now
        if byte_limit > 0 or not truncated:
            words = raw.split()
            if len(words) > max_words:
                truncated = True
                words = words[:max_words]
                raw = " ".join(words)

        # Build notice
        notice = ""
        if truncated:
            notice = f"Truncated at {max_words} words"

        # Numbered lines
        lines = raw.splitlines()
        if numbered:
            content = "\n".join(f"{i + 1} | {line}" for i, line in enumerate(lines))
        else:
            content = "\n".join(lines)

        return True, notice, content

    except Exception as e:
        return False, str(e), ""


def read_single_file_json(path: str, max_words: int = 200_000) -> Dict[str, Any]:
    """Read a single file and return JSON‑compatible dict.

    This is the extracted version of UnifiedFileTools._read_single_file.

    Args:
        path: File path.
        max_words: Maximum words to read.

    Returns:
        Dict with keys "status", "notice", "content".
    """
    success, notice, content = read_file_with_limit(path, max_words=max_words)
    status = "success" if success else "failed"
    return {"status": status, "notice": notice, "content": content}
