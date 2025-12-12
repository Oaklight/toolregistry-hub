"""
Unified file tools matching Kilo Code API.
Implements 7 core functions with atomic ops and safety.
"""

import fnmatch
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from .utils.diff_utility import (
    DiffStyle,
    replace_by_conflict_diff,
    replace_by_unified_diff,
)
from .utils.file_parsing import read_single_file_json
from .utils.filesystem import validate_path


class UnifiedFileTools:
    MAX_WORDS = 200_000  # ~20万单词限制

    @staticmethod
    def read_file(paths: List[str]) -> List[Dict[str, Any]]:
        """Read multiple files using _read_single_file.

        Args:
            paths: List of file paths relative to workspace.

        Returns:
            List of dicts, each with "status", "notice", "content" (numbered).
        """
        return [
            read_single_file_json(path, max_words=UnifiedFileTools.MAX_WORDS)
            for path in paths
        ]

    @staticmethod
    def write_to_file(path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file using atomic replacement via temporary file.

        Args:
            path: Path to the file relative to the workspace directory.
            content: String content to write.

        Returns:
            {"success": True} on success, {"success": False, "error": str} on failure.
        """
        validation = validate_path(path)
        if not validation["valid"]:
            return {"success": False, "error": validation["message"]}

        tmp_path = f"{path}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, path)
            return {"success": True}
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return {"success": False, "error": str(e)}

    @staticmethod
    def insert_content(path: str, line: int, content: str) -> Dict[str, Any]:
        """
        Insert content before a specific line number or append at the end.
        Processes large files efficiently using streaming I/O to minimize memory use.

        Args:
            path: Path to the file relative to the workspace directory.
            line: 1-based line number to insert before (0 to append).
            content: Content to insert (may be multi-line).

        Returns:
            {"success": True, "new_line_count": int} on success,
            {"success": False, "error": str} on failure.
        """
        validation = validate_path(path)
        if not validation["valid"]:
            return {"success": False, "error": validation["message"]}

        try:
            tmp_path = f"{path}.tmp"
            inserted = False  # Tracks whether content was successfully inserted
            line_count = 0  # Counts total lines in the new file

            with open(path, "r", encoding="utf-8", errors="replace") as infile, open(
                tmp_path, "w", encoding="utf-8"
            ) as outfile:
                # Case 1: Append mode (insert at end)
                if line == 0:
                    # Stream all lines unchanged, then write content at the end
                    for line_text in infile:
                        outfile.write(line_text)
                        line_count += 1
                    outfile.write(content)
                    # Update line count for inserted content
                    line_count += content.count("\n") + (
                        1 if not content.endswith("\n") else 0
                    )
                    inserted = True

                else:
                    target = line - 1  # Convert 1-based line to 0-based index
                    # Stream through file and insert content just before the target line
                    for i, line_text in enumerate(infile):
                        if i == target:
                            # Insert new content *before* writing current line
                            outfile.write(content)
                            inserted = True
                        outfile.write(line_text)
                        line_count += 1

                    # Handle insertion at EOF+1 (e.g., valid to insert at line N+1)
                    if not inserted and line == line_count + 1:
                        outfile.write(content)
                        line_count += content.count("\n") + (
                            1 if not content.endswith("\n") else 0
                        )
                        inserted = True

            # Validate that insertion happened correctly
            if not inserted:
                return {
                    "success": False,
                    "error": f"Line {line} out of range (1-{line_count + 1})",
                }

            # Atomically replace original file with updated version
            os.replace(tmp_path, path)
            return {"success": True, "new_line_count": line_count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def apply_diff(
        path: str, diff: str, format: DiffStyle = "unified"
    ) -> Dict[str, Any]:
        """
        Apply a PRECISE, TARGETED modification to a file using a diff in unified or conflict format.
        This is a SURGICAL operation intended for exact, intentional edits — not bulk changes.

        The SEARCH content (in either format) must exactly match the current file content, including whitespace, indentation, and line endings. If you're uncertain about the exact current content, use `read_file` first to retrieve it.

        Args:
            path: Path to the file.
            diff: The diff content as string.
                  - Unified diff: Must follow standard format with ---/+++ headers and @@ hunk markers.
                  - Conflict diff: Must use <<<<<<< SEARCH, =======, >>>>>>> REPLACE markers.
            format: Diff format ("unified" or "conflict"). Defaults to "unified".

        Examples:
            Unified diff:
                --- a/original_file
                +++ b/modified_file
                @@ -1,3 +1,3 @@
                 line1
                -line2
                +line2 modified
                 line3

            Git conflict-style diff:
                <<<<<<< SEARCH
                line2
                =======
                line2 modified
                >>>>>>> REPLACE

        Returns:
            {"success": bool, "format": str} or {"success": False, "error": str}
        """
        validation = validate_path(path)
        if not validation["valid"]:
            return {"success": False, "error": validation["message"]}

        try:
            if format == "unified":
                success = replace_by_unified_diff(path, diff)
            elif format == "conflict":
                success = replace_by_conflict_diff(path, diff)
            else:
                return {
                    "success": False,
                    "error": f"Invalid format, must be one of {DiffStyle}",
                }
            return {"success": success, "format": format}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def search_and_replace(
        path: str,
        search: str,
        replace: str,
        use_regex: bool = False,
        ignore_case: bool = False,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Search and replace text or regex patterns in a file with dry-run preview.

        Args:
            path: Path to the file.
            search: String to search for.
            replace: Replacement string.
            use_regex: Treat search as regex pattern. Defaults to False.
            ignore_case: Ignore case in matching. Defaults to False.
            dry_run: Preview changes without applying. Defaults to True.

        Returns:
            Dict with "preview" (list of changes), "applied_count", "dry_run",
            or {"error": str}.
        """
        # Validate the file path before proceeding
        validation = validate_path(path)
        if not validation["valid"]:
            return {"error": validation["message"]}

        # Prevent unnecessary processing if search and replace are the same
        if search == replace:
            return {
                "error": "Search and replace strings are identical; no changes would be made."
            }

        # Compile regex pattern with optional ignore-case flag if requested
        flags = re.IGNORECASE if ignore_case else 0
        pattern = re.compile(search, flags) if use_regex else None

        try:
            # Read file line by line to preserve line endings and structure
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            preview = []  # Store change previews for reporting
            applied = 0  # Track how many replacements were made
            new_lines = lines.copy()  # Work on a mutable copy

            # Process each line and detect matches
            for i, line in enumerate(lines):
                if pattern:
                    # Use regex substitution if enabled
                    matches = pattern.finditer(line)
                    for m in matches:
                        old = line
                        # Replace only the first match per line (simulates line-level sub)
                        new_line = pattern.sub(replace, line, count=1)
                        preview.append(
                            {
                                "line": i + 1,
                                "old": old.rstrip(),
                                "new": new_line.rstrip(),
                            }
                        )
                        if not dry_run:
                            new_lines[i] = new_line
                            applied += 1
                else:
                    # Perform literal string search and replace
                    if search in line:
                        old = line
                        new_line = line.replace(search, replace)
                        preview.append(
                            {
                                "line": i + 1,
                                "old": old.rstrip(),
                                "new": new_line.rstrip(),
                            }
                        )
                        if not dry_run:
                            new_lines[i] = new_line
                            applied += 1

            # Only write back to file if not in dry-run mode
            if not dry_run:
                new_content = "".join(new_lines)
                tmp_path = f"{path}.tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                # Atomically replace original file with updated version
                os.replace(tmp_path, path)

            return {
                "preview": preview,
                "applied_count": applied if not dry_run else 0,
                "dry_run": dry_run,
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def search_files(
        dir_path: str, regex: str, file_pattern: str = "*", context_lines: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Recursively search for a regex pattern across files in a directory.

        Args:
            dir_path: Directory path to search (relative to workspace).
            regex: Regular expression pattern to match.
            file_pattern: Glob pattern to filter files (e.g., "*.py"). Defaults to "*".
            context_lines: Number of surrounding lines for context. Defaults to 2.

        Returns:
            List[Dict[str, Any]] of matches with file, line_num, line, context.
        """
        validation = validate_path(dir_path)
        if not validation["valid"]:
            return [{"error": validation["message"]}]

        pattern = re.compile(regex)
        results = []

        for root, dirs, files in os.walk(dir_path):
            for filename in files:
                if not fnmatch.fnmatch(filename, file_pattern):
                    continue
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                except:
                    continue

                for i, line in enumerate(lines):
                    if pattern.search(line):
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context = [
                            (ln + 1, lines[ln].rstrip("\n"))
                            for ln in range(start, end)
                            if ln != i
                        ]
                        results.append(
                            {
                                "file": file_path,
                                "line_num": i + 1,
                                "line": line.rstrip("\n"),
                                "context": context,
                            }
                        )
        return results

    @staticmethod
    def list_files(
        dir_path: str, recursive: bool = False, show_hidden: bool = False
    ) -> List[str]:
        """
        List files and directories in a path.

        Args:
            dir_path: Directory path.
            recursive: Recurse into subdirectories. Defaults to False.
            show_hidden: Show hidden files/directories. Defaults to False.

        Returns:
            List[str] of relative paths (recursive) or basenames (top-level),
            or ["Error: message"] on invalid path.
        """
        validation = validate_path(dir_path)
        if not validation["valid"]:
            return [f"Error: {validation['message']}"]

        p = Path(dir_path)
        if not p.is_dir():
            return []

        if recursive:
            items = [
                str(rel) for rel in p.rglob("*") if not rel.is_dir() or show_hidden
            ]  # Files + dirs if hidden?
            # Adjust for hidden
            items = []
            for rel in p.rglob("*"):
                if show_hidden or not rel.name.startswith("."):
                    items.append(str(rel.relative_to(p)))
        else:
            items = []
            for child in p.iterdir():
                if show_hidden or not child.name.startswith("."):
                    items.append(child.name)

        return items
