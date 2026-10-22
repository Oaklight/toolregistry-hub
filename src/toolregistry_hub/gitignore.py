"""Minimal ``.gitignore`` support for the file search tools.

Implements the subset of git's ignore syntax that matters for filtering search
results, with **no external dependency** (no ``pathspec``, no ``git``
subprocess), so it keeps working in sandboxes where neither is available.

Supported syntax:

- blank lines and ``#`` comments (``\\#`` escapes a leading dot/hash),
- ``!`` negation (``\\!`` escapes a literal ``!``),
- trailing ``/`` for directory-only rules,
- leading ``/`` and any interior ``/`` anchoring the rule to the
  ``.gitignore`` file that contains it,
- ``*`` and ``?`` that do not cross ``/``,
- ``**`` for any number of directories (``a/**/b``, ``**/x``, ``y/**``),
- character classes such as ``[abc]`` and ``[!abc]``,
- hierarchical files: rules from the repository root down to the searched
  directory are applied in order, so the deepest file wins.

Like git, a path under an ignored directory cannot be re-included by a
negation rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_IGNORE_FILE = ".gitignore"
_ALWAYS_IGNORED = ".git"


@dataclass(frozen=True)
class _Rule:
    """One compiled ``.gitignore`` line.

    Attributes:
        regex: Pattern matched against the path relative to ``base``.
        base: Directory of the ``.gitignore`` file, relative to the anchor.
        negated: ``True`` for an ``!`` rule, which re-includes the path.
        directory_only: ``True`` when the rule ended with ``/``.
    """

    regex: re.Pattern[str]
    base: tuple[str, ...]
    negated: bool
    directory_only: bool


def _strip_comment_and_spaces(line: str) -> str:
    """Remove a trailing newline and unescaped trailing spaces.

    Args:
        line: One raw line from a ``.gitignore`` file.

    Returns:
        The line with the newline removed and trailing spaces that are not
        escaped by a backslash stripped.
    """
    line = line.rstrip("\r\n")
    while line.endswith(" ") and not line.endswith("\\ "):
        line = line[:-1]
    return line


def _translate_star(pattern: str, index: int) -> tuple[str, int]:
    """Translate the ``*`` run that starts at *index*.

    Args:
        pattern: The pattern being translated.
        index: Position of the first ``*``.

    Returns:
        A ``(regex_source, next_index)`` pair.
    """
    if not pattern.startswith("**", index):
        return "[^/]*", index + 1
    if pattern.startswith("**/", index):
        return "(?:[^/]+/)*", index + 3
    return ".*", index + 2


def _translate_class(pattern: str, index: int) -> tuple[str, int]:
    """Translate the ``[...]`` class that starts at *index*.

    Args:
        pattern: The pattern being translated.
        index: Position of the opening ``[``.

    Returns:
        A ``(regex_source, next_index)`` pair; an unterminated class becomes a
        literal ``[``.
    """
    end = pattern.find("]", index + 1)
    if end == -1:
        return re.escape("["), index + 1
    body = pattern[index + 1 : end]
    if body.startswith("!"):
        body = "^" + body[1:]
    return "[" + body.replace("\\", "\\\\") + "]", end + 1


def _translate(pattern: str) -> str:
    """Translate one gitignore pattern to regular-expression source.

    Args:
        pattern: The pattern body, without a leading ``/`` or a trailing
            ``/``.

    Returns:
        Regex source that matches the path relative to the rule's directory.
    """
    out: list[str] = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            piece, index = _translate_star(pattern, index)
        elif char == "?":
            piece, index = "[^/]", index + 1
        elif char == "[":
            piece, index = _translate_class(pattern, index)
        elif char == "\\" and index + 1 < len(pattern):
            piece, index = re.escape(pattern[index + 1]), index + 2
        else:
            piece, index = re.escape(char), index + 1
        out.append(piece)
    return "".join(out)


def _compile_rule(line: str, base: tuple[str, ...]) -> _Rule | None:
    """Compile one ``.gitignore`` line.

    Args:
        line: One raw line.
        base: Directory of the ``.gitignore`` file, relative to the anchor.

    Returns:
        The compiled rule, or ``None`` for a blank line or comment.
    """
    pattern = _strip_comment_and_spaces(line)
    if not pattern:
        return None
    if pattern.startswith("\\#") or pattern.startswith("\\!"):
        pattern = pattern[1:]
    elif pattern.startswith("#"):
        return None

    negated = pattern.startswith("!")
    if negated:
        pattern = pattern[1:]
    if not pattern:
        return None

    directory_only = pattern.endswith("/")
    pattern = pattern.rstrip("/")
    if not pattern:
        return None

    anchored = pattern.startswith("/") or "/" in pattern
    pattern = pattern.lstrip("/")
    body = _translate(pattern)
    source = "^" + body + "$" if anchored else r"(?:^|.*/)" + body + "$"
    return _Rule(
        regex=re.compile(source),
        base=base,
        negated=negated,
        directory_only=directory_only,
    )


def _find_git_root(start: Path) -> Path | None:
    """Return the nearest ancestor of *start* that contains a ``.git`` entry."""
    for directory in (start, *start.parents):
        if (directory / _ALWAYS_IGNORED).exists():
            return directory
    return None


class GitIgnoreFilter:
    """Ignore rules collected from ``.gitignore`` files around a directory.

    Rules are loaded lazily, one directory at a time, so a ``.gitignore`` deep
    in the tree applies to the paths below it without walking the whole tree
    up front.

    Attributes:
        anchor: Directory the collected rules are relative to.
    """

    def __init__(self, anchor: Path) -> None:
        """Create a filter rooted at *anchor*.

        Args:
            anchor: Directory the ``.gitignore`` files are relative to.
        """
        self.anchor = anchor
        self._dir_rules: dict[Path, list[_Rule]] = {}

    @classmethod
    def for_path(
        cls, start: Path, *, require_repo: bool = True
    ) -> GitIgnoreFilter | None:
        """Return a filter for searches under *start*.

        Args:
            start: Directory (or file) whose searches should honour ignore
                rules.
            require_repo: Return ``None`` when *start* is not inside a git
                repository.  ``False`` still honours ``.gitignore`` files
                found under *start*, which keeps an explicit
                ``respect_gitignore=True`` useful outside a checkout.

        Returns:
            A filter anchored at the repository root, or ``None`` when
            *start* is not in a repository and *require_repo* is set.
        """
        start = start.resolve()
        if start.is_file():
            start = start.parent
        git_root = _find_git_root(start)
        if git_root is None:
            if require_repo:
                return None
            return cls(start)
        return cls(git_root)

    def is_ignored(self, path: Path, *, is_dir: bool | None = None) -> bool:
        """Whether *path* is excluded by the collected rules.

        Every ancestor is evaluated too, matching git's rule that a path under
        an ignored directory cannot be re-included.

        Args:
            path: Absolute or resolvable path to test.
            is_dir: Whether *path* is a directory.  Detected from the
                filesystem when omitted.

        Returns:
            ``True`` when the path should be excluded from search results.
        """
        try:
            relative = path.resolve().relative_to(self.anchor)
        except ValueError:
            return False
        parts = relative.parts
        if not parts:
            return False
        if _ALWAYS_IGNORED in parts:
            return True
        if is_dir is None:
            is_dir = path.is_dir()

        rules = self._rules_up_to(parts[:-1])
        for length in range(1, len(parts) + 1):
            sub_parts = parts[:length]
            sub_is_dir = is_dir if length == len(parts) else True
            matched = _last_match(rules, sub_parts, sub_is_dir)
            if matched is not None and not matched.negated:
                return True
        return False

    def _rules_up_to(self, directory_parts: tuple[str, ...]) -> list[_Rule]:
        """Collect rules from the anchor down to *directory_parts*.

        Args:
            directory_parts: Components of the directory containing the tested
                path, relative to :attr:`anchor`.

        Returns:
            Rules in application order: ancestors first, the deepest
            ``.gitignore`` last.
        """
        rules: list[_Rule] = []
        directory = self.anchor
        prefixes = [()]
        for index in range(len(directory_parts)):
            prefixes.append(directory_parts[: index + 1])
        for base in prefixes:
            directory = self.anchor.joinpath(*base) if base else self.anchor
            rules.extend(self._rules_in(directory, base))
        return rules

    def _rules_in(self, directory: Path, base: tuple[str, ...]) -> list[_Rule]:
        """Return the rules declared by *directory*'s ``.gitignore``.

        Args:
            directory: Directory to read.
            base: Components of *directory* relative to :attr:`anchor`.

        Returns:
            Compiled rules; empty when the file is absent or unreadable.
        """
        if directory in self._dir_rules:
            return self._dir_rules[directory]
        compiled: list[_Rule] = []
        try:
            text = (directory / _IGNORE_FILE).read_text(errors="replace")
        except OSError:
            text = ""
        for line in text.splitlines():
            rule = _compile_rule(line, base)
            if rule is not None:
                compiled.append(rule)
        self._dir_rules[directory] = compiled
        return compiled


def _last_match(
    rules: list[_Rule], parts: tuple[str, ...], is_dir: bool
) -> _Rule | None:
    """Return the last rule matching *parts*, or ``None``.

    Args:
        rules: Rules in application order.
        parts: Path components relative to the anchor.
        is_dir: Whether the tested path is a directory.

    Returns:
        The winning rule, if any.
    """
    winner: _Rule | None = None
    for rule in rules:
        if len(rule.base) >= len(parts):
            continue
        if parts[: len(rule.base)] != rule.base:
            continue
        if rule.directory_only and not is_dir:
            continue
        rest = "/".join(parts[len(rule.base) :])
        if rest and rule.regex.fullmatch(rest):
            winner = rule
    return winner
