"""Unit tests for FileOps."""

import os
import tempfile

import pytest

from toolregistry_hub.file_ops import FileOps


class TestFileOps:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        self.test_content = "Hello, World!\nThis is a test file.\nLine 3\n"
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(self.test_content)

    def teardown_method(self):
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_read_file_single(self):
        result = FileOps.read_file([self.test_file])
        assert len(result) == 1
        item = result[0]
        assert item["status"] == "success"
        # # content is numbered lines
        # assert "1 | Hello, World!" in item["content"]
        # content is non-numbered lines
        assert "Hello, World!" in item["content"]
        assert item["notice"] == ""

    def test_read_file_multiple(self):
        file2 = os.path.join(self.temp_dir, "file2.txt")
        with open(file2, "w") as f:
            f.write("Second file")
        results = FileOps.read_file([self.test_file, file2])
        assert len(results) == 2
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "success"

    def test_read_file_truncated_by_words(self):
        # 生成超过20万单词的内容
        words = ["word"] * 250_000  # 25万单词
        huge_content = " ".join(words)
        huge_file = os.path.join(self.temp_dir, "huge.txt")
        with open(huge_file, "w") as f:
            f.write(huge_content)
        result = FileOps.read_file([huge_file])
        assert len(result) == 1
        item = result[0]
        assert item["status"] == "success"
        assert "Truncated at 200000 words" in item["notice"]
        # 确保内容被截断（行数有限）
        lines = item["content"].splitlines()
        assert len(lines) > 0

    def test_write_to_file(self):
        new_file = os.path.join(self.temp_dir, "new.txt")
        new_content = "New content"
        result = FileOps.write_to_file(new_file, new_content)
        assert result["success"]
        assert os.path.exists(new_file)
        read_result = FileOps.read_file([new_file])
        assert read_result[0]["status"] == "success"
        # content includes line numbers, strip them for comparison
        content_lines = read_result[0]["content"].splitlines()
        if content_lines:
            actual = "\n".join(
                line.split(" | ", 1)[1] if " | " in line else line
                for line in content_lines
            )
        else:
            actual = ""
        assert actual == new_content

    def test_insert_content_append(self):
        result = FileOps.insert_content(self.test_file, 0, "Appended\n")
        assert result["success"]
        read_result = FileOps.read_file([self.test_file])
        content_lines = read_result[0]["content"].splitlines()
        # last line should be "Appended"
        last_line = content_lines[-1] if content_lines else ""
        # strip line number prefix
        if " | " in last_line:
            last_line = last_line.split(" | ", 1)[1]
        assert last_line == "Appended"

    def test_insert_content_line2(self):
        result = FileOps.insert_content(self.test_file, 2, "Inserted\n")
        assert result["success"]
        read_result = FileOps.read_file([self.test_file])
        content_lines = read_result[0]["content"].splitlines()
        # line 2 (1-indexed) should be "Inserted"
        line2 = content_lines[1] if len(content_lines) > 1 else ""
        if " | " in line2:
            line2 = line2.split(" | ", 1)[1]
        assert line2 == "Inserted"

    def test_insert_content_invalid_line(self):
        result = FileOps.insert_content(self.test_file, 10, "Invalid")
        assert not result["success"]

    def test_apply_diff_unified(self):
        FileOps.write_to_file(self.test_file, "line1\nline2\nline3\n")
        diff = """--- a/test.txt
+++ b/test.txt
@@ -1,3 +1,3 @@
 line1
-line2
+new line2
 line3"""
        result = FileOps.apply_diff(self.test_file, diff, "unified")
        assert result["success"]
        read_result = FileOps.read_file([self.test_file])
        content = read_result[0]["content"]
        assert "new line2" in content

    def test_apply_diff_git(self):
        FileOps.write_to_file(self.test_file, "old\nline3\n")
        diff = """<<<<<<< SEARCH
old
=======
new
>>>>>>> REPLACE"""
        result = FileOps.apply_diff(self.test_file, diff, "conflict")
        assert result["success"]
        read_result = FileOps.read_file([self.test_file])
        content = read_result[0]["content"]
        assert "new" in content and "old" not in content

    def test_search_and_replace_literal(self):
        result = FileOps.search_and_replace(
            self.test_file, "World", "Kilo", dry_run=True
        )
        assert len(result["preview"]) > 0
        assert result["dry_run"]

        result = FileOps.search_and_replace(
            self.test_file, "World", "Kilo", dry_run=False
        )
        assert result["applied_count"] > 0
        read_result = FileOps.read_file([self.test_file])
        content = read_result[0]["content"]
        assert "Kilo" in content

    def test_search_and_replace_regex(self):
        result = FileOps.search_and_replace(
            self.test_file, r"L\w+", "LINE", use_regex=True, dry_run=False
        )
        assert result["applied_count"] > 0

    def test_search_files(self):
        file2 = os.path.join(self.temp_dir, "file2.txt")
        with open(file2, "w") as f:
            f.write("test match")
        results = FileOps.search_files(self.temp_dir, "test")
        assert len(results) > 0
        assert "context" in results[0]

    def test_list_files(self):
        subdir = os.path.join(self.temp_dir, "sub")
        os.mkdir(subdir)
        results = FileOps.list_files(self.temp_dir, recursive=False)
        assert "test.txt" in results
        assert "sub" in results

        rec = FileOps.list_files(self.temp_dir, recursive=True)
        assert len(rec) > 0
