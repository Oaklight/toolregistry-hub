"""Tests for ``.gitignore`` support in the file search tools (#73)."""

from __future__ import annotations

from pathlib import Path

import pytest
from toolregistry import Tool

from toolregistry_hub.file_search import FileSearch
from toolregistry_hub.gitignore import GitIgnoreFilter


def _write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


@pytest.fixture
def repo(tmp_path):
    """A small checkout with a root and a nested .gitignore."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("build/\n*.log\n!keep.log\n/root-secret.txt\n")
    _write(
        tmp_path,
        {
            "src/main.py": "TODO: fix\n",
            "src/util.py": "pass\n",
            "build/out.py": "generated\n",
            "build/nested/deep.py": "generated\n",
            "a.log": "noise\n",
            "keep.log": "important\n",
            "root-secret.txt": "root secret\n",
            "sub/secret.txt": "anchored here\n",
            "sub/local.txt": "local\n",
            "node_modules/pkg/index.js": "dependency\n",
        },
    )
    (tmp_path / "sub" / ".gitignore").write_text("/local.txt\n")
    return tmp_path


@pytest.fixture
def plain_tree(tmp_path):
    """A directory that is not a git checkout but has a .gitignore."""
    tmp_path.joinpath(".gitignore").write_text("*.tmp\n")
    _write(tmp_path, {"keep.py": "x\n", "scratch.tmp": "x\n", "sub/other.tmp": "x\n"})
    return tmp_path


def _names(results: list[dict]) -> set[str]:
    return {entry["file"] for entry in results}


class TestGlob:
    def test_ignored_paths_are_excluded(self, repo):
        found = set(FileSearch.glob("**/*", root=str(repo)))
        assert "src/main.py" in found
        assert "build/out.py" not in found
        assert "a.log" not in found
        assert "root-secret.txt" not in found
        assert "node_modules/pkg/index.js" in found

    def test_negation_reincludes(self, repo):
        found = set(FileSearch.glob("*.log", root=str(repo)))
        assert found == {"keep.log"}

    def test_nested_gitignore_applies(self, repo):
        found = set(FileSearch.glob("sub/*", root=str(repo)))
        assert "sub/secret.txt" in found
        assert "sub/local.txt" not in found

    def test_filter_can_be_disabled(self, repo):
        found = set(
            FileSearch.glob("**/*.log", root=str(repo), respect_gitignore=False)
        )
        assert found == {"a.log", "keep.log"}

    def test_outside_a_repository_no_filter_by_default(self, plain_tree):
        found = set(FileSearch.glob("**/*.tmp", root=str(plain_tree)))
        assert found == {"scratch.tmp", "sub/other.tmp"}

    def test_explicit_true_outside_a_repository_filters(self, plain_tree):
        assert (
            FileSearch.glob("**/*.tmp", root=str(plain_tree), respect_gitignore=True)
            == []
        )

    def test_no_gitignore_is_a_no_op(self, tmp_path):
        _write(tmp_path, {"a.py": "x\n"})
        assert FileSearch.glob("*.py", root=str(tmp_path)) == ["a.py"]


class TestGrep:
    def test_ignored_files_are_skipped(self, repo):
        results = FileSearch.grep("TODO|generated|noise", path=str(repo))
        assert _names(results) == {"src/main.py"}

    def test_nested_gitignore_applies(self, repo):
        results = FileSearch.grep("anchored", path=str(repo))
        assert _names(results) == {"sub/secret.txt"}

    def test_explicit_file_is_always_searched(self, repo):
        results = FileSearch.grep("noise", path=str(repo / "a.log"))
        assert _names(results) == {"a.log"}

    def test_filter_can_be_disabled(self, repo):
        results = FileSearch.grep("noise", path=str(repo), respect_gitignore=False)
        assert _names(results) == {"a.log"}


class TestTree:
    def test_ignored_entries_are_hidden(self, repo):
        output = FileSearch.tree(str(repo))
        assert "src" in output
        assert "build/" not in output
        assert "a.log" not in output
        assert "keep.log" in output
        assert "root-secret.txt" not in output
        assert "node_modules" in output

    def test_filter_can_be_disabled(self, repo):
        output = FileSearch.tree(str(repo), respect_gitignore=False)
        assert "build/" in output
        assert "a.log" in output

    def test_outside_a_repository_no_filter_by_default(self, plain_tree):
        assert "scratch.tmp" in FileSearch.tree(str(plain_tree))
        assert "scratch.tmp" not in FileSearch.tree(
            str(plain_tree), respect_gitignore=True
        )


class TestPatterns:
    def test_double_star_matches_any_depth(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("**/cache/**\n")
        _write(
            tmp_path, {"a/cache/x.txt": "x\n", "cache/y.txt": "x\n", "b/z.txt": "x\n"}
        )
        flt = GitIgnoreFilter.for_path(tmp_path)
        assert flt.is_ignored(tmp_path / "a/cache/x.txt")
        assert flt.is_ignored(tmp_path / "cache/y.txt")
        assert not flt.is_ignored(tmp_path / "b/z.txt")

    def test_question_mark_and_class_do_not_cross_directories(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("file?.txt\n[abc].md\n")
        _write(
            tmp_path,
            {"file1.txt": "x\n", "file10.txt": "x\n", "a.md": "x\n", "d.md": "x\n"},
        )
        flt = GitIgnoreFilter.for_path(tmp_path)
        assert flt.is_ignored(tmp_path / "file1.txt")
        assert not flt.is_ignored(tmp_path / "file10.txt")
        assert flt.is_ignored(tmp_path / "a.md")
        assert not flt.is_ignored(tmp_path / "d.md")

    def test_anchored_pattern_matches_only_at_root(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("/top.txt\n")
        _write(tmp_path, {"top.txt": "x\n", "sub/top.txt": "x\n"})
        flt = GitIgnoreFilter.for_path(tmp_path)
        assert flt.is_ignored(tmp_path / "top.txt")
        assert not flt.is_ignored(tmp_path / "sub/top.txt")

    def test_git_directory_is_always_ignored(self, tmp_path):
        (tmp_path / ".git").mkdir()
        _write(tmp_path, {".git/config": "x\n"})
        flt = GitIgnoreFilter.for_path(tmp_path)
        assert flt.is_ignored(tmp_path / ".git" / "config")

    def test_require_repo_outside_a_checkout(self, tmp_path):
        (tmp_path / ".gitignore").write_text("*.tmp\n")
        assert GitIgnoreFilter.for_path(tmp_path) is None
        assert GitIgnoreFilter.for_path(tmp_path, require_repo=False) is not None

    def test_paths_outside_the_anchor_are_not_ignored(self, tmp_path):
        repo = tmp_path / "repo"
        (repo / ".git").mkdir(parents=True)
        (repo / ".gitignore").write_text("*.py\n")
        outside = tmp_path / "outside.py"
        outside.write_text("x\n")
        flt = GitIgnoreFilter.for_path(repo)
        assert not flt.is_ignored(outside)

    def test_comments_and_blank_lines_are_ignored(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("# comment\n\n*.tmp\n")
        _write(tmp_path, {"a.tmp": "x\n"})
        flt = GitIgnoreFilter.for_path(tmp_path)
        assert flt.is_ignored(tmp_path / "a.tmp")


class TestToolSchema:
    def test_parameter_describes_the_override(self):
        """The model must see that the filter can be turned off per call."""
        for method in (FileSearch.glob, FileSearch.grep, FileSearch.tree):
            tool = Tool.from_function(method)
            spec = tool.parameters["properties"]["respect_gitignore"]
            assert spec["type"] == "boolean"
            assert "false returns ignored paths" in spec["description"]
