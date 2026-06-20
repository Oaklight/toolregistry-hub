"""Unit tests for FileOps module."""

import os
import tempfile

import pytest

from toolregistry_hub.file_ops import FileOps


class TestFileOps:
    """Test cases for FileOps class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        self.test_content = "Hello, World!\nThis is a test file.\nLine 3"

        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(self.test_content)

    def teardown_method(self):
        """Clean up test environment after each test."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _read(self, path: str | None = None) -> dict[str, str | bool]:
        return FileOps.read(path or self.test_file)

    # ── read ─────────────────────────────────────────────────────────────

    def test_read(self):
        result = self._read()
        assert result["content"] == self.test_content
        assert isinstance(result["digest"], str)
        assert result["is_symlink"] is False
        assert result["real_path"] == os.path.realpath(self.test_file)

    def test_read_not_found(self):
        with pytest.raises(FileNotFoundError):
            FileOps.read(os.path.join(self.temp_dir, "missing.txt"))

    def test_read_symlink_allowed(self):
        link_path = os.path.join(self.temp_dir, "link.txt")
        os.symlink(self.test_file, link_path)
        result = FileOps.read(link_path)
        assert result["content"] == self.test_content
        assert result["is_symlink"] is True
        assert result["real_path"] == os.path.realpath(self.test_file)

    # ── write ────────────────────────────────────────────────────────────

    def test_write_new_file_without_digest(self):
        new_file = os.path.join(self.temp_dir, "new.txt")
        result = FileOps.write(new_file, "new content")
        assert isinstance(result["digest"], str)
        assert FileOps.read(new_file)["content"] == "new content"

    def test_write_existing_requires_digest(self):
        with pytest.raises(ValueError, match="digest is required"):
            FileOps.write(self.test_file, "new content")

    def test_write_existing_with_digest(self):
        digest = self._read()["digest"]
        result = FileOps.write(self.test_file, "new content", digest=digest)
        assert isinstance(result["digest"], str)
        assert self._read()["content"] == "new content"

    def test_write_rejects_stale_digest(self):
        digest = self._read()["digest"]
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("external change")
        with pytest.raises(ValueError, match="changed since digest"):
            FileOps.write(self.test_file, "new content", digest=digest)

    def test_write_append_mode(self):
        digest = self._read()["digest"]
        result = FileOps.write(
            self.test_file, "\nappended", digest=digest, mode="append"
        )
        assert isinstance(result["digest"], str)
        assert self._read()["content"] == self.test_content + "\nappended"

    def test_write_append_preserves_utf8_bom(self):
        bom = b"\xef\xbb\xbf"
        with open(self.test_file, "wb") as f:
            f.write(bom + b"line1\n")
        digest = self._read()["digest"]
        FileOps.write(self.test_file, "line2\n", digest=digest, mode="append")
        with open(self.test_file, "rb") as f:
            raw = f.read()
        assert raw.startswith(bom)
        assert b"line1\nline2\n" in raw

    def test_write_invalid_mode(self):
        with pytest.raises(ValueError, match="mode must"):
            FileOps.write(os.path.join(self.temp_dir, "new.txt"), "content", mode="bad")

    def test_write_rejects_symlink(self):
        link_path = os.path.join(self.temp_dir, "link.txt")
        os.symlink(self.test_file, link_path)
        with pytest.raises(ValueError, match="Refusing to write through symlink"):
            FileOps.write(link_path, "new content")

    def test_write_rejects_tmp_symlink(self):
        new_file = os.path.join(self.temp_dir, "new.txt")
        tmp_link = f"{new_file}.tmp"
        os.symlink(self.test_file, tmp_link)
        with pytest.raises(ValueError, match="Refusing to write through symlink"):
            FileOps.write(new_file, "new content")

    # ── edit ─────────────────────────────────────────────────────────────

    def test_edit_requires_digest(self):
        with pytest.raises(ValueError, match="digest is required"):
            FileOps.edit(self.test_file, "Hello", "Hi", digest=None)  # type: ignore[arg-type]

    def test_edit_single_match(self):
        digest = self._read()["digest"]
        result = FileOps.edit(self.test_file, "Hello", "Hi", digest=digest)
        assert "diff" in result
        assert isinstance(result["digest"], str)
        assert self._read()["content"].startswith("Hi, World!")

    def test_edit_digest_can_chain_multiple_edits(self):
        digest = self._read()["digest"]
        first = FileOps.edit(self.test_file, "Hello", "Hi", digest=digest)
        second = FileOps.edit(
            self.test_file, "World", "Universe", digest=first["digest"]
        )
        assert isinstance(second["digest"], str)
        assert self._read()["content"].startswith("Hi, Universe!")

    def test_edit_rejects_stale_digest(self):
        digest = self._read()["digest"]
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("external change")
        with pytest.raises(ValueError, match="changed since digest"):
            FileOps.edit(self.test_file, "external", "new", digest=digest)

    def test_edit_no_match(self):
        digest = self._read()["digest"]
        with pytest.raises(ValueError, match="not found"):
            FileOps.edit(self.test_file, "missing", "replacement", digest=digest)

    def test_edit_multiple_matches_replace_all(self):
        FileOps.write(self.test_file, "TODO 1\nTODO 2\n", digest=self._read()["digest"])
        digest = self._read()["digest"]
        FileOps.edit(self.test_file, "TODO", "DONE", digest=digest, replace_all=True)
        assert self._read()["content"] == "DONE 1\nDONE 2\n"

    def test_edit_multiple_matches_start_line(self):
        content = "TODO first\nline\nTODO second\n"
        FileOps.write(self.test_file, content, digest=self._read()["digest"])
        digest = self._read()["digest"]
        FileOps.edit(self.test_file, "TODO", "DONE", digest=digest, start_line=3)
        result = self._read()["content"]
        assert "TODO first" in result
        assert "DONE second" in result

    def test_edit_multiple_matches_no_disambiguation(self):
        FileOps.write(self.test_file, "dup\ndup\n", digest=self._read()["digest"])
        digest = self._read()["digest"]
        with pytest.raises(ValueError, match="2 times"):
            FileOps.edit(self.test_file, "dup", "unique", digest=digest)

    def test_edit_identical_strings(self):
        digest = self._read()["digest"]
        with pytest.raises(ValueError, match="identical"):
            FileOps.edit(self.test_file, "same", "same", digest=digest)

    def test_edit_empty_old_string(self):
        digest = self._read()["digest"]
        with pytest.raises(ValueError, match="must not be empty"):
            FileOps.edit(self.test_file, "", "something", digest=digest)

    def test_edit_preserves_crlf(self):
        with open(self.test_file, "wb") as f:
            f.write(b"line1\r\nline2\r\n")
        digest = self._read()["digest"]
        FileOps.edit(self.test_file, "line2", "changed", digest=digest)
        with open(self.test_file, "rb") as f:
            assert f.read() == b"line1\r\nchanged\r\n"

    def test_edit_preserves_lf(self):
        with open(self.test_file, "wb") as f:
            f.write(b"line1\nline2\n")
        digest = self._read()["digest"]
        FileOps.edit(self.test_file, "line2", "changed", digest=digest)
        with open(self.test_file, "rb") as f:
            raw = f.read()
        assert b"\r\n" not in raw
        assert raw == b"line1\nchanged\n"

    def test_edit_preserves_utf8_bom(self):
        bom = b"\xef\xbb\xbf"
        with open(self.test_file, "wb") as f:
            f.write(bom + b"line1\n")
        digest = self._read()["digest"]
        FileOps.edit(self.test_file, "line1", "changed", digest=digest)
        with open(self.test_file, "rb") as f:
            raw = f.read()
        assert raw.startswith(bom)
        assert b"changed" in raw

    def test_edit_delete_string(self):
        digest = self._read()["digest"]
        FileOps.edit(self.test_file, "This is a test file.\n", "", digest=digest)
        assert self._read()["content"] == "Hello, World!\nLine 3"

    def test_edit_rejects_symlink(self):
        link_path = os.path.join(self.temp_dir, "link.txt")
        os.symlink(self.test_file, link_path)
        digest = self._read()["digest"]
        with pytest.raises(ValueError, match="Refusing to write through symlink"):
            FileOps.edit(link_path, "Hello", "Hi", digest=digest)

    def test_edit_rejects_tmp_symlink(self):
        digest = self._read()["digest"]
        tmp_link = f"{self.test_file}.tmp"
        os.symlink(self.test_file, tmp_link)
        with pytest.raises(ValueError, match="Refusing to write through symlink"):
            FileOps.edit(self.test_file, "Hello", "Hi", digest=digest)

    # ── internal utilities ───────────────────────────────────────────────

    def test_make_diff(self):
        diff = FileOps._make_diff("a\nb", "a\nc")
        assert "-b" in diff
        assert "+c" in diff

    def test_make_git_conflict(self):
        conflict = FileOps._make_git_conflict("ours", "theirs")
        assert "<<<<<<< HEAD" in conflict
        assert "ours" in conflict
        assert "theirs" in conflict
