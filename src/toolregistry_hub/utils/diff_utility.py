"""Utility functions for working with diffs and applying patches.

This module provides functionality for generating and applying both unified diffs
(similar to Unix `diff -u`) and conflict diffs (similar to Git merge conflicts).
It leverages Python's built-in `difflib` module for diff generation and provides
utilities for parsing and applying these diffs to files.

The module includes:
- Functions to generate unified and conflict-style diffs between strings
- Functions to generate context diffs (similar to Unix `diff -c`)
- Functions to calculate similarity ratios between strings
- Functions to find close matches for strings
- Classes to represent diff hunks and conflict blocks
- Functions to parse diff strings into structured objects
- Functions to apply diffs to files atomically

Example usage:
    >>> from diff_utility import diff_unified, replace_by_unified_diff
    >>> original = "line1\\nline2\\nline3"
    >>> modified = "line1\\nline2 changed\\nline3"
    >>> diff = diff_unified(original, modified)
    >>> print(diff)
    ---
    +++
    @@ -1,3 +1,3 @@
    line1
    -line2
    +line2 changed
    line3
"""

import dataclasses
import difflib
import os
import re
from typing import List, Literal, Tuple

from typing_extensions import TypeAlias

DiffStyle: TypeAlias = Literal["unified", "conflict"]

# ======================================================================
# styled diff generation helpers
# ======================================================================


def diff_unified(ours: str, theirs: str) -> str:
    """Generate a unified diff between two strings.

    This function creates a unified diff format showing the differences
    between two strings, similar to the output of the Unix `diff -u` command.

    Args:
        ours: The original string to compare.
        theirs: The modified string to compare against the original.

    Returns:
        A string containing the unified diff output with no line terminators.

    Example:
        >>> original = "line1\\nline2\\nline3"
        >>> modified = "line1\\nline2 changed\\nline3"
        >>> print(diff_unified(original, modified))
        ---
        +++
        @@ -1,3 +1,3 @@
        line1
        -line2
        +line2 changed
        line3
    """
    return "\n".join(
        difflib.unified_diff(ours.splitlines(), theirs.splitlines(), lineterm="")
    )


def diff_context(ours: str, theirs: str, n: int = 3) -> str:
    """Generate a context diff between two strings.

    This function creates a context diff format showing the differences
    between two strings, similar to the output of the Unix `diff -c` command.
    Context diffs include more surrounding context lines than unified diffs.

    Args:
        ours: The original string to compare.
        theirs: The modified string to compare against the original.
        n: Number of context lines to include around changes (default: 3).

    Returns:
        A string containing the context diff output with no line terminators.

    Example:
        >>> original = "line1\\nline2\\nline3\\nline4\\nline5"
        >>> modified = "line1\\nline2 changed\\nline3\\nline4\\nline5"
        >>> print(diff_context(original, modified))
        ***
        ---
        ***************
        *** 1,5 ****
        ! line1
        ! line2
          line3
          line4
          line5
        \------- 1,5 ----
        ! line1
        ! line2 changed
          line3
          line4
          line5
    """
    return "\n".join(
        difflib.context_diff(ours.splitlines(), theirs.splitlines(), lineterm="", n=n)
    )


def diff_conflict(ours: str, theirs: str) -> str:
    """Generate a conflict-block-style diff between two strings.

    This function creates a conflict-block diff format that shows both versions
    of the content, similar to what shows when there are merge conflicts.

    Args:
        ours: The original string (typically from the current branch).
        theirs: The modified string (typically from the incoming branch).

    Returns:
        A string containing the conflict-block diff with markers indicating
        the boundaries between the two versions.

    Example:
        >>> original = "line1\\nline2\\nline3"
        >>> modified = "line1\\nline2 changed\\nline3"
        >>> print(diff_conflict(original, modified))
        <<<<<<< HEAD
        line1
        line2
        line3
        =======
        line1
        line2 changed
        line3
        >>>>>>> incoming
    """
    return f"<<<<<<< HEAD\n{ours}\n=======\n{theirs}\n>>>>>>> incoming\n"


# ======================================================================
# Quick Similarity Helpers
# ======================================================================


def get_similarity_ratio(ours: str, theirs: str) -> float:
    """Calculate the similarity ratio between two strings.

    This function uses difflib's SequenceMatcher to calculate a similarity
    ratio between 0.0 and 1.0, where 1.0 means the strings are identical.

    Args:
        ours: The first string to compare.
        theirs: The second string to compare.

    Returns:
        A float between 0.0 and 1.0 representing the similarity ratio.

    Example:
        >>> original = "Hello World"
        >>> modified = "Hello World!"
        >>> ratio = get_similarity_ratio(original, modified)
        >>> ratio > 0.9
        True
    """
    matcher = difflib.SequenceMatcher(None, ours, theirs)
    return matcher.ratio()


def get_close_matches(
    word: str, possibilities: List[str], n: int = 3, cutoff: float = 0.6
) -> List[str]:
    """Get the best matches for a word from a list of possibilities.

    This function uses difflib's get_close_matches to find the best matches
    for a given word from a list of possibilities.

    Args:
        word: The word to find matches for.
        possibilities: A list of strings to search for matches.
        n: Maximum number of close matches to return (default: 3).
        cutoff: A float in [0, 1] representing the minimum similarity ratio
                required for a match to be considered (default: 0.6).

    Returns:
        A list of the best matches, sorted by similarity.

    Example:
        >>> words = ["apple", "banana", "orange", "grape", "pineapple"]
        >>> matches = get_close_matches("app", words)
        >>> "apple" in matches
        True
    """
    return difflib.get_close_matches(word, possibilities, n=n, cutoff=cutoff)


# ======================================================================
# Unified Hunk styled diff utilities
# ======================================================================


@dataclasses.dataclass
class Hunk:
    """Represents a single unified-diff hunk.

    A hunk is a contiguous block of lines in a unified diff that shows
    the changes between the original and modified versions of a file.

    Attributes:
        orig_start: 1-based starting line number in the original file.
        orig_len: Number of lines in the original file for this hunk.
        new_start: 1-based starting line number in the new file.
        new_len: Number of lines in the new file for this hunk.
        lines: List of diff lines inside this hunk (including +/- prefixes).
    """

    orig_start: int  # 1-based start line in original file
    orig_len: int  # number of lines in original
    new_start: int  # 1-based start line in new file
    new_len: int  # number of lines in new
    lines: List[str]  # diff lines inside this hunk (incl. +/-)


def _parse_unified_diff(diff: str) -> Tuple[List[Hunk], List[str]]:
    """Parse a unified diff string and extract hunk objects and context lines.

    This function processes a unified diff format string and extracts
    individual hunks along with any leading context lines that don't
    belong to any hunk.

    Args:
        diff: A string containing the unified diff content.

    Returns:
        A tuple containing:
            - List of Hunk objects representing the parsed hunks.
            - List of context lines that appear before any hunk.

    Example:
        >>> diff_content = '''--- a/file.txt
        ... +++ b/file.txt
        ... @@ -1,3 +1,3 @@
        ...  line1
        ... -line2
        ... +line2 changed
        ...  line3'''
        >>> hunks, context = _parse_unified_diff(diff_content)
        >>> len(hunks)
        1
        >>> hunks[0].orig_start
        1
    """
    hunk_regex = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
    hunks: List[Hunk] = []
    context: List[str] = []
    lines = diff.splitlines(keepends=True)

    i = 0
    while i < len(lines):
        m = hunk_regex.match(lines[i])
        if not m:
            context.append(lines[i])
            i += 1
            continue

        orig_start = int(m.group(1))
        orig_len = int(m.group(2) or 1)
        new_start = int(m.group(3))
        new_len = int(m.group(4) or 1)

        hunk_lines: List[str] = []
        i += 1
        while i < len(lines) and not hunk_regex.match(lines[i]):
            hunk_lines.append(lines[i])
            i += 1

        hunks.append(Hunk(orig_start, orig_len, new_start, new_len, hunk_lines))

    return hunks, context


def replace_by_unified_diff(path: str, diff: str) -> bool:
    """Apply a unified diff to a file, modifying it in place.

    This function reads a file from the given path, applies the unified diff
    to it, and writes the result back to the same path. The operation is
    atomic - it writes to a temporary file first and then replaces the
    original file.

    Args:
        path: Path to the file to modify.
        diff: A string containing the unified diff to apply.

    Returns:
        True if the operation was successful, False otherwise.

    Raises:
        Any exceptions during file I/O are caught and result in False being returned.

    Example:
        >>> with open('test.txt', 'w') as f:
        ...     f.write('line1\\nline2\\nline3\\n')
        >>> diff_content = '''--- a/test.txt
        ... +++ b/test.txt
        ... @@ -1,3 +1,3 @@
        ...  line1
        ... -line2
        ... +line2 changed
        ...  line3'''
        >>> replace_by_unified_diff('test.txt', diff_content)
        True
        >>> with open('test.txt') as f:
        ...     print(f.read())
        line1
        line2 changed
        line3
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            original_lines = f.readlines()

        hunks, _ = _parse_unified_diff(diff)

        patched_lines: List[str] = []
        orig_pos = 0

        for h in hunks:
            # copy unchanged prefix
            patched_lines.extend(original_lines[orig_pos : h.orig_start - 1])
            orig_pos = h.orig_start - 1

            # apply hunk
            for hl in h.lines:
                if hl.startswith(" "):
                    patched_lines.append(original_lines[orig_pos])
                    orig_pos += 1
                elif hl.startswith("-"):
                    orig_pos += 1
                elif hl.startswith("+"):
                    patched_lines.append(hl[1:])
                else:
                    raise ValueError(f"Invalid diff line: {hl}")

        # trailing unchanged lines
        patched_lines.extend(original_lines[orig_pos:])

        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.writelines(patched_lines)
        os.replace(tmp_path, path)
        return True
    except Exception:
        return False


# ======================================================================
# Git ConflictBlock styled diff utilities
# ======================================================================


@dataclasses.dataclass
class ConflictBlock:
    """Represents a single Git conflict block.

    A conflict block contains the markers and content from both sides
    of a merge conflict, allowing for programmatic resolution.

    Attributes:
        incoming_marker: The incoming marker line (e.g., '<<<<<<< HEAD').
        incoming_lines: List of lines from the incoming version.
        separator: The separator line ('=======').
        current_lines: List of lines from the current version.
        end_marker: The end marker line (e.g., '>>>>>>> branch').
    """

    incoming_marker: str  # e.g. '<<<<<<< HEAD'
    incoming_lines: List[str]
    separator: str  # '======='
    current_lines: List[str]
    end_marker: str  # e.g. '>>>>>>> branch'


def _parse_conflict_diff(diff: str) -> List[ConflictBlock]:
    """Parse a conflict diff string and extract ConflictBlock objects.

    This function processes a conflict diff format string and extracts
    individual conflict blocks, each containing both sides of the conflict.

    Args:
        diff: A string containing the conflict diff content.

    Returns:
        A list of ConflictBlock objects representing the parsed conflict blocks.

    Example:
        >>> conflict_content = '''<<<<<<< HEAD
        ... line1
        ... line2
        ... =======
        ... line1
        ... line2 changed
        ... >>>>>>> incoming'''
        >>> blocks = _parse_conflict_diff(conflict_content)
        >>> len(blocks)
        1
        >>> blocks[0].incoming_lines
        ['line1\\n', 'line2\\n']
    """
    start_re = re.compile(r"^<<<<<<< (.+)$")
    sep_re = re.compile(r"^=======$")
    end_re = re.compile(r"^>>>>>>> (.+)$")

    blocks: List[ConflictBlock] = []
    lines = diff.splitlines(keepends=True)

    i = 0
    while i < len(lines):
        m_start = start_re.match(lines[i])
        if not m_start:
            i += 1
            continue

        incoming_marker = m_start.group(0)
        i += 1
        incoming: List[str] = []
        while i < len(lines) and not sep_re.match(lines[i]):
            incoming.append(lines[i])
            i += 1
        if i >= len(lines):
            break
        separator = lines[i]

        i += 1
        current: List[str] = []
        while i < len(lines) and not end_re.match(lines[i]):
            current.append(lines[i])
            i += 1
        if i >= len(lines):
            break
        end_marker = lines[i]

        blocks.append(
            ConflictBlock(
                incoming_marker=incoming_marker,
                incoming_lines=incoming,
                separator=separator,
                current_lines=current,
                end_marker=end_marker,
            )
        )
        i += 1

    return blocks


def replace_by_conflict_diff(path: str, diff: str) -> bool:
    """Apply a conflict diff to a file, resolving conflicts by choosing one side.

    This function reads a file from the given path, applies the conflict diff
    to it, and writes the result back to the same path. It resolves conflicts
    by replacing the incoming side with the current side. The operation is
    atomic - it writes to a temporary file first and then replaces the
    original file.

    Args:
        path: Path to the file to modify.
        diff: A string containing the conflict diff to apply.

    Returns:
        True if the operation was successful, False otherwise.

    Raises:
        Any exceptions during file I/O are caught and result in False being returned.

    Example:
        >>> with open('test.txt', 'w') as f:
        ...     f.write('<<<<<<< HEAD\\nline1\\nline2\\n=======\\nline1\\nline2 changed\\n>>>>>>> incoming\\n')
        >>> conflict_content = '''<<<<<<< HEAD
        ... line1
        ... line2
        ... =======
        ... line1
        ... line2 changed
        ... >>>>>>> incoming'''
        >>> replace_by_conflict_diff('test.txt', conflict_content)
        True
        >>> with open('test.txt') as f:
        ...     print(f.read())
        line1
        line2
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            original_lines = f.readlines()

        blocks = _parse_conflict_diff(diff)

        patched_lines: List[str] = []
        orig_pos = 0

        # Walk through original lines; when we hit a conflict location, skip
        # the original "incoming" chunk and insert the "current" chunk instead.
        for blk in blocks:
            # copy everything up to the conflict
            patched_lines.extend(
                original_lines[orig_pos : orig_pos + len(blk.incoming_lines)]
            )
            orig_pos += len(blk.incoming_lines)

            # replace with the chosen side (current_lines)
            patched_lines.extend(blk.current_lines)

        # trailing unchanged lines
        patched_lines.extend(original_lines[orig_pos:])

        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.writelines(patched_lines)
        os.replace(tmp_path, path)
        return True
    except Exception:
        return False
