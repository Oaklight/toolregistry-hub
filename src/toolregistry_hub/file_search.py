"""File and content search tools.

Provides glob-based file finding, regex content search (grep), and directory
tree display — the three most common file-discovery operations in agent
workflows.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

# Hard caps to prevent oversized returns
_MAX_GLOB_RESULTS = 1000
_MAX_GREP_RESULTS = 200
_MAX_TREE_ENTRIES = 2000


class FileSearch:
    """File and content search tools."""

    @staticmethod
    def glob(
        pattern: str,
        root: str = ".",
        recursive: bool = True,
    ) -> list[str]:
        """Find files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g. ``"**/*.py"``, ``"src/**/*.ts"``).
            root: Root directory to search from. Defaults to current directory.
            recursive: Whether ``**`` matches subdirectories. Defaults to True.

        Returns:
            List of matching file paths relative to *root*, sorted by
            modification time (most recent first).  Capped at 1000 results.

        Raises:
            FileNotFoundError: If *root* does not exist or is not a directory.
        """
        root_path = Path(root).resolve()
        if not root_path.is_dir():
            raise FileNotFoundError(
                f"Root is not a directory or does not exist: {root}"
            )

        if recursive:
            matches = list(root_path.glob(pattern))
        else:
            # Non-recursive: only match in the root directory itself
            matches = [p for p in root_path.glob(pattern) if p.parent == root_path]

        # Sort by modification time, most recent first
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Cap results
        matches = matches[:_MAX_GLOB_RESULTS]

        return [str(p.relative_to(root_path)) for p in matches]

    @staticmethod
    def grep(
        pattern: str,
        path: str = ".",
        recursive: bool = True,
        file_pattern: str | None = None,
        max_results: int = 50,
    ) -> list[dict]:
        """Search file contents using regex.

        Args:
            pattern: Regex pattern to search for.
            path: File or directory to search in. Defaults to current directory.
            recursive: Whether to search subdirectories. Defaults to True.
            file_pattern: Optional glob to filter files (e.g. ``"*.py"``).
            max_results: Maximum number of match results to return.
                Clamped to an internal cap of 200.

        Returns:
            List of dicts, each with keys:

            - ``file`` (str): path relative to search root
            - ``line_number`` (int): 1-based line number
            - ``content`` (str): the matching line (stripped)

        Raises:
            FileNotFoundError: If *path* does not exist.
            re.error: If *pattern* is not a valid regex.
        """
        target = Path(path).resolve()
        if not target.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        regex = re.compile(pattern)
        effective_max = min(max_results, _MAX_GREP_RESULTS)
        results: list[dict] = []

        if target.is_file():
            FileSearch._grep_file(target, regex, target.parent, results, effective_max)
            return results

        # Directory search
        if recursive:
            files = target.rglob("*")
        else:
            files = target.iterdir()

        for filepath in sorted(files):
            if len(results) >= effective_max:
                break
            if not filepath.is_file():
                continue
            if file_pattern and not fnmatch.fnmatch(filepath.name, file_pattern):
                continue
            FileSearch._grep_file(filepath, regex, target, results, effective_max)

        return results

    @staticmethod
    def _grep_file(
        filepath: Path,
        regex: re.Pattern,
        base: Path,
        results: list[dict],
        max_results: int,
    ) -> None:
        """Search a single file for regex matches.

        Args:
            filepath: File to search.
            regex: Compiled regex pattern.
            base: Base directory for relative path calculation.
            results: Accumulator list to append matches to.
            max_results: Stop after this many total results.
        """
        try:
            text = filepath.read_text(errors="replace")
        except (OSError, PermissionError):
            return

        for line_num, line in enumerate(text.splitlines(), start=1):
            if len(results) >= max_results:
                return
            if regex.search(line):
                results.append(
                    {
                        "file": str(filepath.relative_to(base)),
                        "line_number": line_num,
                        "content": line.strip(),
                    }
                )

    @staticmethod
    def tree(
        path: str = ".",
        max_depth: int = 3,
        show_hidden: bool = False,
        file_pattern: str | None = None,
    ) -> str:
        """Display directory tree structure.

        Args:
            path: Root directory. Defaults to current directory.
            max_depth: Maximum depth to display. Defaults to 3.
            show_hidden: Whether to show hidden files/directories.
            file_pattern: Optional glob to filter displayed files.

        Returns:
            Tree-formatted string representation of the directory.

        Raises:
            FileNotFoundError: If *path* does not exist or is not a directory.
            ValueError: If *max_depth* is less than 1.
        """
        root = Path(path).resolve()
        if not root.is_dir():
            raise FileNotFoundError(
                f"Path is not a directory or does not exist: {path}"
            )
        if max_depth < 1:
            raise ValueError("max_depth must be 1 or greater.")

        lines: list[str] = [root.name + "/"]
        count = [0]  # mutable counter for the nested function

        FileSearch._build_tree(
            root, "", max_depth, 1, show_hidden, file_pattern, lines, count
        )

        if count[0] >= _MAX_TREE_ENTRIES:
            lines.append(f"\n... truncated at {_MAX_TREE_ENTRIES} entries")

        return "\n".join(lines)

    @staticmethod
    def _list_entries(
        directory: Path,
        show_hidden: bool,
        file_pattern: str | None,
    ) -> list[Path]:
        """List and filter directory entries for tree display.

        Sorts directories first, then by name.  Filters hidden entries
        and applies optional file glob pattern (directories always pass
        so the tree structure stays intact).

        Args:
            directory: Directory to list.
            show_hidden: Whether to include hidden entries.
            file_pattern: Optional glob to filter files.

        Returns:
            Sorted, filtered list of entries, or empty list on
            permission error.
        """
        try:
            entries = sorted(
                directory.iterdir(), key=lambda e: (not e.is_dir(), e.name)
            )
        except PermissionError:
            return []

        if not show_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]

        if file_pattern:
            entries = [
                e
                for e in entries
                if e.is_dir() or fnmatch.fnmatch(e.name, file_pattern)
            ]

        return entries

    @staticmethod
    def _build_tree(
        directory: Path,
        prefix: str,
        max_depth: int,
        current_depth: int,
        show_hidden: bool,
        file_pattern: str | None,
        lines: list[str],
        count: list[int],
    ) -> None:
        """Recursively build tree lines.

        Args:
            directory: Current directory to list.
            prefix: Indentation prefix for the current level.
            max_depth: Maximum depth to display.
            current_depth: Current recursion depth.
            show_hidden: Whether to show hidden entries.
            file_pattern: Optional glob to filter files.
            lines: Accumulator for output lines.
            count: Single-element list used as a mutable counter.
        """
        if current_depth > max_depth:
            return

        entries = FileSearch._list_entries(directory, show_hidden, file_pattern)

        for i, entry in enumerate(entries):
            if count[0] >= _MAX_TREE_ENTRIES:
                return

            is_last = i == len(entries) - 1
            connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{connector}{entry.name}{suffix}")
            count[0] += 1

            if entry.is_dir() and current_depth < max_depth:
                extension = "    " if is_last else "\u2502   "
                FileSearch._build_tree(
                    entry,
                    prefix + extension,
                    max_depth,
                    current_depth + 1,
                    show_hidden,
                    file_pattern,
                    lines,
                    count,
                )
