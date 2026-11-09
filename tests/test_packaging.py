"""Packaging invariants the published wheel must satisfy.

These guard the bare ``pip install toolregistry-hub`` path, which the unit
suite cannot exercise because the development environment already has the
core library installed.  ``tomllib`` is used where it exists; Python 3.10,
which the package still supports, has no TOML parser, so the arrays are
extracted as text there.
"""

import re
from pathlib import Path

try:  # Python 3.11+; the package still supports 3.10.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on 3.10
    tomllib = None

ROOT = Path(__file__).resolve().parent.parent


def _runtime_dependencies() -> str:
    """Return the body of the ``[project]`` ``dependencies`` array."""
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(
        r"^dependencies = \[(.*?)^\]", pyproject, re.MULTILINE | re.DOTALL
    )
    assert match is not None, "pyproject.toml has no [project] dependencies array"
    return match.group(1)


def _extra_requirements(extra: str) -> list[str]:
    """Return the requirement strings in one ``optional-dependencies`` extra.

    A TOML parser is preferred.  Python 3.10 ships without ``tomllib``, so
    the array is extracted as text there; an extra is a flat list of
    strings, which that extraction covers.
    """
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if tomllib is not None:
        data = tomllib.loads(pyproject)
        return list(data["project"]["optional-dependencies"][extra])
    match = re.search(
        rf"^{re.escape(extra)} = \[(.*?)^\]",
        pyproject,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"pyproject.toml has no {extra} extra"
    return re.findall(r'"([^"]+)"', match.group(1))


def test_core_library_is_a_runtime_dependency() -> None:
    """Every tool imports ``toolregistry``, so the bare install must pull it."""
    body = _runtime_dependencies()
    assert re.search(r'"toolregistry\b', body), (
        "toolregistry must be in [project].dependencies, not only in an "
        f"extra; bare installs then fail on 'import toolregistry_hub': {body!r}"
    )


def test_server_openapi_extra_installs_the_gateway_backend() -> None:
    """``server_openapi`` must pull the server's gateway extra.

    The Hub's ``openapi`` command is served through the gateway, so the
    extra names ``toolregistry-server[gateway]`` (which carries FastAPI and
    uvicorn) instead of duplicating the backend packages.
    """
    requirements = _extra_requirements("server_openapi")
    assert any(
        requirement.startswith("toolregistry-server[gateway]")
        for requirement in requirements
    ), requirements
