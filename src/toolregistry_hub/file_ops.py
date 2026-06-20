"""Atomic file operations toolkit for LLM agents."""

import difflib
import hashlib
import os
from typing import Literal


class FileOps:
    """Core file operations with read/edit/write safety semantics."""

    # ======================
    #  Internal Helpers
    # ======================

    @staticmethod
    def _detect_encoding(raw: bytes) -> tuple[str, bytes]:
        """Detect file encoding from BOM bytes."""
        if raw.startswith(b"\xef\xbb\xbf"):
            return ("utf-8-sig", b"")
        if raw.startswith(b"\xff\xfe"):
            return ("utf-16-le", b"\xff\xfe")
        if raw.startswith(b"\xfe\xff"):
            return ("utf-16-be", b"\xfe\xff")
        return ("utf-8", b"")

    @staticmethod
    def _detect_line_ending(text: str) -> str:
        """Detect dominant line ending in text."""
        crlf_count = text.count("\r\n")
        lf_count = text.count("\n") - crlf_count
        return "\r\n" if crlf_count > lf_count else "\n"

    @staticmethod
    def _real_path(path: str) -> str:
        """Return absolute real path."""
        return os.path.realpath(os.path.abspath(path))

    @staticmethod
    def _digest(raw: bytes) -> str:
        """Return SHA-256 digest for file content."""
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _read_raw(path: str) -> bytes:
        """Read file as bytes."""
        with open(path, "rb") as f:
            return f.read()

    @staticmethod
    def _decode(raw: bytes) -> tuple[str, str, bytes]:
        """Decode raw bytes preserving encoding metadata."""
        encoding, bom = FileOps._detect_encoding(raw)
        text = raw[len(bom) :].decode(encoding) if bom else raw.decode(encoding)
        return text, encoding, bom

    @staticmethod
    def _assert_not_symlink(path: str) -> None:
        """Reject writes through symlinks."""
        if os.path.islink(path):
            raise ValueError(
                f"Refusing to write through symlink: {path}. "
                "Resolve the symlink and pass the real target path explicitly."
            )

    @staticmethod
    def _assert_digest(path: str, digest: str | None, raw: bytes) -> None:
        """Require and verify digest for existing file modifications."""
        if digest is None:
            raise ValueError(
                f"digest is required for existing file: {path}. "
                "Call read(path) first and pass the returned digest."
            )
        if digest != FileOps._digest(raw):
            raise ValueError("File changed since digest was issued; read it again")

    # ======================
    #  Public Tools
    # ======================

    @staticmethod
    def read(path: str) -> dict[str, str | bool]:
        """Read text file content and return a digest for safe edits/writes.

        Symlinks are allowed for reading. Writes through symlinks are rejected,
        so callers should pass ``real_path`` to ``edit`` or ``write`` when
        ``is_symlink`` is true.

        Args:
            path: File path to read.

        Returns:
            Dict with ``content``, ``digest``, ``is_symlink``, and ``real_path``.
        """
        raw = FileOps._read_raw(path)
        text, _encoding, _bom = FileOps._decode(raw)
        return {
            "content": text,
            "digest": FileOps._digest(raw),
            "is_symlink": os.path.islink(path),
            "real_path": FileOps._real_path(path),
        }

    @staticmethod
    def edit(
        path: str,
        old_string: str,
        new_string: str,
        digest: str,
        replace_all: bool = False,
        start_line: int | None = None,
    ) -> dict[str, str]:
        """Replace exact string in file.

        Args:
            path: Absolute path to file.
            old_string: Exact text to find. Must not be empty.
            new_string: Replacement text (must differ from old_string).
            digest: SHA-256 digest returned by ``read(path)``.
            replace_all: Replace all occurrences instead of just one.
            start_line: Optional 1-based line number hint for disambiguation.

        Returns:
            Dict with ``diff`` and updated ``digest``.
        """
        if not old_string:
            raise ValueError("old_string must not be empty")
        if old_string == new_string:
            raise ValueError("old_string and new_string are identical")
        FileOps._assert_not_symlink(path)

        raw = FileOps._read_raw(path)
        FileOps._assert_digest(path, digest, raw)

        text, encoding, bom = FileOps._decode(raw)
        line_ending = FileOps._detect_line_ending(text)

        content = text.replace("\r\n", "\n")
        old_str = old_string.replace("\r\n", "\n")
        new_str = new_string.replace("\r\n", "\n")

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

        diff_output = "\n".join(
            difflib.unified_diff(
                content.splitlines(), new_content.splitlines(), lineterm=""
            )
        )

        if line_ending == "\r\n":
            new_content = new_content.replace("\n", "\r\n")

        encoded = bom + new_content.encode(encoding)
        tmp_path = f"{path}.tmp"
        FileOps._assert_not_symlink(tmp_path)
        with open(tmp_path, "wb") as f:
            f.write(encoded)
        os.replace(tmp_path, path)

        return {"diff": diff_output, "digest": FileOps._digest(encoded)}

    @staticmethod
    def write(
        path: str,
        content: str,
        digest: str | None = None,
        mode: Literal["overwrite", "append"] = "overwrite",
    ) -> dict[str, str]:
        """Write content to a file.

        Existing files require a digest from ``read(path)``.  New files can be
        created without a digest.  ``mode="append"`` appends content without
        requiring the caller to provide the full original file content.

        Args:
            path: Destination file path.
            content: Content to write or append.
            digest: Required when the file already exists.
            mode: ``"overwrite"`` or ``"append"``.

        Returns:
            Dict with updated ``digest``.
        """
        if mode not in {"overwrite", "append"}:
            raise ValueError('mode must be "overwrite" or "append"')
        FileOps._assert_not_symlink(path)

        existing = b""
        if os.path.exists(path):
            existing = FileOps._read_raw(path)
            FileOps._assert_digest(path, digest, existing)

        if mode == "append" and existing:
            existing_text, encoding, bom = FileOps._decode(existing)
            raw = bom + (existing_text + content).encode(encoding)
        else:
            raw = content.encode("utf-8")

        tmp_path = f"{path}.tmp"
        FileOps._assert_not_symlink(tmp_path)
        with open(tmp_path, "wb") as f:
            f.write(raw)
        os.replace(tmp_path, path)

        return {"digest": FileOps._digest(raw)}

    # ======================
    #  Internal Utilities
    # ======================

    @staticmethod
    def _make_diff(ours: str, theirs: str) -> str:
        """Generate unified diff text between two strings."""
        return "\n".join(
            difflib.unified_diff(ours.splitlines(), theirs.splitlines(), lineterm="")
        )

    @staticmethod
    def _make_git_conflict(ours: str, theirs: str) -> str:
        """Generate git merge conflict marker text between two strings."""
        return f"<<<<<<< HEAD\n{ours}\n=======\n{theirs}\n>>>>>>> incoming\n"
