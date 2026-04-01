"""
file_ops.py - Atomic file operations toolkit for LLM agents

Key features:
- All methods are static for stateless usage
- Atomic writes with automatic backups
- Unified error handling
- Exact string replacement with disambiguation support
- Encoding and line ending preservation
"""

import difflib
import fnmatch
import os
import re


class FileOps:
    """Core file operations toolkit designed for LLM agent integration.

    Handles file reading, atomic writing, appending, searching, and exact
    string replacement for file editing.
    """

    # ======================
    #  Internal Helpers
    # ======================

    @staticmethod
    def _detect_encoding(raw: bytes) -> tuple[str, bytes]:
        """Detect file encoding from BOM bytes.

        Args:
            raw: Raw file bytes.

        Returns:
            Tuple of (encoding_name, bom_bytes). For utf-8-sig the codec
            handles BOM transparently so bom is empty.
        """
        if raw.startswith(b"\xef\xbb\xbf"):
            return ("utf-8-sig", b"")
        if raw.startswith(b"\xff\xfe"):
            return ("utf-16-le", b"\xff\xfe")
        if raw.startswith(b"\xfe\xff"):
            return ("utf-16-be", b"\xfe\xff")
        return ("utf-8", b"")

    @staticmethod
    def _detect_line_ending(text: str) -> str:
        """Detect dominant line ending in text.

        Args:
            text: Decoded file content.

        Returns:
            '\\r\\n' if CRLF is dominant, otherwise '\\n'.
        """
        crlf_count = text.count("\r\n")
        lf_count = text.count("\n") - crlf_count
        return "\r\n" if crlf_count > lf_count else "\n"

    # ======================
    #  Content Modification
    # ======================

    @staticmethod
    def edit(
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        start_line: int | None = None,
    ) -> str:
        """Replace exact string in file.

        Args:
            file_path: Absolute path to file.
            old_string: Exact text to find. Must not be empty.
            new_string: Replacement text (must differ from old_string).
            replace_all: Replace all occurrences instead of just one.
            start_line: Optional 1-based line number hint for disambiguation.
                When multiple matches exist, selects the match whose start
                line is closest to this value. Does not require exact precision.

        Returns:
            Unified diff showing what changed (for display purposes).

        Raises:
            ValueError: If old_string is empty, identical to new_string,
                not found, or ambiguous without start_line/replace_all.
            FileNotFoundError: If file_path does not exist.
        """
        if not old_string:
            raise ValueError("old_string must not be empty")
        if old_string == new_string:
            raise ValueError("old_string and new_string are identical")

        # Read file as bytes to preserve encoding
        with open(file_path, "rb") as f:
            raw = f.read()

        encoding, bom = FileOps._detect_encoding(raw)
        if bom:
            text = raw[len(bom) :].decode(encoding)
        else:
            text = raw.decode(encoding)

        line_ending = FileOps._detect_line_ending(text)

        # Normalize to \n for matching
        content = text.replace("\r\n", "\n")
        old_str = old_string.replace("\r\n", "\n")
        new_str = new_string.replace("\r\n", "\n")

        # Find all non-overlapping occurrences
        positions: list[int] = []
        start = 0
        while True:
            idx = content.find(old_str, start)
            if idx == -1:
                break
            positions.append(idx)
            start = idx + len(old_str)

        n = len(positions)
        if n == 0:
            raise ValueError("old_string not found in file")

        if n == 1:
            pos = positions[0]
            new_content = content[:pos] + new_str + content[pos + len(old_str) :]
        elif replace_all:
            new_content = content.replace(old_str, new_str)
        elif start_line is not None:

            def _pos_to_line(pos: int) -> int:
                return content[:pos].count("\n") + 1

            match_lines = [(pos, _pos_to_line(pos)) for pos in positions]
            closest = min(match_lines, key=lambda x: abs(x[1] - start_line))
            pos = closest[0]
            new_content = content[:pos] + new_str + content[pos + len(old_str) :]
        else:
            raise ValueError(
                f"old_string found {n} times in file. Use replace_all=True to "
                f"replace all occurrences, or provide start_line to disambiguate."
            )

        # Generate diff for display (on normalized content)
        diff_output = FileOps.make_diff(content, new_content)

        # Restore line endings
        if line_ending == "\r\n":
            new_content = new_content.replace("\n", "\r\n")

        # Encode back
        encoded = bom + new_content.encode(encoding)

        # Atomic write (binary)
        tmp_path = f"{file_path}.tmp"
        with open(tmp_path, "wb") as f:
            f.write(encoded)
        os.replace(tmp_path, file_path)

        return diff_output

    @staticmethod
    def search_files(path: str, regex: str, file_pattern: str = "*") -> list[dict]:
        """Perform regex search across files in a directory, returning matches with context.

        Args:
            path: The directory path to search recursively.
            regex: The regex pattern to search for.
            file_pattern: Glob pattern to filter files (default='*').

        Returns:
            List of dicts with keys:
                - file: file path
                - line_num: line number of match (1-based)
                - line: matched line content
                - context: list of context lines (tuples of line_num, line content)
        """

        pattern = re.compile(regex)
        results = []
        context_radius = 2  # lines before and after match to include as context

        for root, dirs, files in os.walk(path):
            for filename in files:
                if not fnmatch.fnmatch(filename, file_pattern):
                    continue
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                except Exception:
                    continue

                for i, line in enumerate(lines):
                    if pattern.search(line):
                        start_context = max(0, i - context_radius)
                        end_context = min(len(lines), i + context_radius + 1)
                        context_lines = [
                            (ln + 1, lines[ln].rstrip("\n"))
                            for ln in range(start_context, end_context)
                            if ln != i
                        ]
                        results.append(
                            {
                                "file": file_path,
                                "line_num": i + 1,
                                "line": line.rstrip("\n"),
                                "context": context_lines,
                            }
                        )
        return results

    # ======================
    #  File I/O Operations
    # ======================

    @staticmethod
    def read_file(path: str) -> str:
        """Read text file content.

        Args:
            path: File path to read

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If path doesn't exist
            UnicodeError: On encoding failures
        """
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()

    @staticmethod
    def write_file(path: str, content: str) -> None:
        """Atomically write content to a text file (overwrite). Creates the file if it doesn't exist.

        Args:
            path: Destination file path
            content: Content to write
        """
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)

    @staticmethod
    def append_file(path: str, content: str) -> None:
        """Append content to a text file. Creates the file if it doesn't exist.

        Args:
            path: Destination file path
            content: Content to append
        """
        # Use 'a' mode for appending, creates file if it doesn't exist
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)

    # ======================
    #  Content Generation
    # ======================

    @staticmethod
    def make_diff(ours: str, theirs: str) -> str:
        """Generate unified diff text between two strings.

        Args:
            ours: The 'ours' version string.
            theirs: The 'theirs' version string.

        Note:
            Intended for comparison/visualization, not direct modification.
            not for direct text modification tasks.

        Returns:
            Unified diff text
        """
        return "\n".join(
            difflib.unified_diff(ours.splitlines(), theirs.splitlines(), lineterm="")
        )

    @staticmethod
    def make_git_conflict(ours: str, theirs: str) -> str:
        """Generate git merge conflict marker text between two strings.

        Args:
            ours: The 'ours' version string.
            theirs: The 'theirs' version string.

        Note:
            Intended for comparison/visualization, not direct modification.
            not for direct text modification tasks.

        Returns:
            Text with conflict markers
        """
        return f"<<<<<<< HEAD\n{ours}\n=======\n{theirs}\n>>>>>>> incoming\n"

    # ======================
    #  Safety Utilities
    # ======================

    @staticmethod
    def validate_path(path: str) -> dict[str, bool | str]:
        """Validate file path safety (checks for empty paths, dangerous characters).

        Args:
            path: The path string to validate.

        Returns:
            Dictionary with keys:
            - valid (bool): Path safety status
            - message (str): Description if invalid
        """
        if not path:
            return {"valid": False, "message": "Empty path"}
        if "~" in path:
            path = os.path.expanduser(path)
        if any(c in path for c in '*?"><|'):
            return {"valid": False, "message": "Contains dangerous characters"}
        return {"valid": True, "message": ""}
