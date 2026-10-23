"""Packaging invariants the published wheel must satisfy.

These guard the bare ``pip install toolregistry-hub`` path, which the unit
suite cannot exercise because the development environment already has the
core library installed. The file is parsed as text so the test also runs on
Python 3.10, where ``tomllib`` does not exist.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _runtime_dependencies() -> str:
    """Return the body of the ``[project]`` ``dependencies`` array."""
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(
        r"^dependencies = \[(.*?)^\]", pyproject, re.MULTILINE | re.DOTALL
    )
    assert match is not None, "pyproject.toml has no [project] dependencies array"
    return match.group(1)


def test_core_library_is_a_runtime_dependency() -> None:
    """Every tool imports ``toolregistry``, so the bare install must pull it."""
    body = _runtime_dependencies()
    assert re.search(r'"toolregistry\b', body), (
        "toolregistry must be in [project].dependencies, not only in an "
        f"extra; bare installs then fail on 'import toolregistry_hub': {body!r}"
    )
