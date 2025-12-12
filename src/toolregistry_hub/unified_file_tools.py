"""
Unified file tools matching Kilo Code API.
Implements 7 core functions with atomic ops and safety.
"""

import fnmatch
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from .utils.diff_utility import (
    DiffStyle,
    replace_by_conflict_diff,
    replace_by_unified_diff,
)
from .utils.filesystem import validate_path


class UnifiedFileTools:
    MAX_READ_SIZE = 1048576  # 1MB

    @staticmethod
    def read_file(path: str, max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Read the contents of a file with an optional size limit.

        Args:
            path: Path to the file relative to the workspace directory.
            max_size: Optional maximum number of bytes to read. Defaults to 1MB.

        Returns:
            Dict[str, Any] containing file info or {"error": str} on failure.
        """
        validation = validate_path(path)
        if not validation["valid"]:
            return {"error": validation["message"]}

        max_size = max_size or UnifiedFileTools.MAX_READ_SIZE
        try:
            stat = os.stat(path)
            size = stat.st_size
            truncated = size > max_size

            with open(path, "r", encoding="utf-8", errors="replace") as f:
                if truncated:
                    f.read(max_size)
                    content = f.read()[:max_size]  # Wait, better chunk read
                    # Simple: read all, slice if large
                    content = f.read()
                    if len(content.encode("utf-8")) > max_size:
                        content = content[: max_size // 4]  # Rough char limit
                        truncated = True
                else:
                    content = f.read()

            lines = content.splitlines()
            return {
                "content": content,
                "truncated": truncated,
                "size": size,
                "line_count": len(lines),
            }
        except Exception as e:
            return {"error": str(e)}

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
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            if line == 0:
                lines.append(content)
            elif 1 <= line <= len(lines) + 1:
                lines.insert(line - 1, content)
            else:
                return {
                    "success": False,
                    "error": f"Line {line} out of range (1-{len(lines) + 1})",
                }

            new_content = "".join(lines)
            tmp_path = f"{path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            os.replace(tmp_path, path)
            return {"success": True, "new_line_count": len(lines)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def apply_diff(
        path: str, diff: str, format: DiffStyle = "unified"
    ) -> Dict[str, Any]:
        """
        Apply a unified or conflict format diff to a file.

        Args:
            path: Path to the file.
            diff: The diff content as string. Unified diff text (must use standard format with ---/+++ headers and @@ hunk markers), or Git conflict style diff text (using <<<<<<< SEARCH, =======, >>>>>>> REPLACE markers).
            format: Diff format ("unified" or "conflict"). Defaults to "unified".

        Examples:
            - Unified diff text:
                --- a/original_file
                +++ b/modified_file
                @@ -1,3 +1,3 @@
                -line2
                +line2 modified
            - git conflict diff text:
                <<<<<<< SEARCH
                line2
                =======
                line2 modified
                >>>>>>> REPLACE

        Returns:
            {"success": bool, "format": str} or {"success": False, "error": str}.
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
        validation = validate_path(path)
        if not validation["valid"]:
            return {"error": validation["message"]}

        flags = re.IGNORECASE if ignore_case else 0
        pattern = re.compile(search, flags) if use_regex else None

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            preview = []
            applied = 0
            new_lines = lines.copy()

            for i, line in enumerate(lines):
                if pattern:
                    matches = pattern.finditer(line)
                    for m in matches:
                        old = line
                        new_line = pattern.sub(
                            replace, line, count=1
                        )  # First match or global?
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

            if not dry_run:
                new_content = "".join(new_lines)
                tmp_path = f"{path}.tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
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
