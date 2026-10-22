"""Importing a test module must not load a developer's `.env` (#210).

`tests/websearch/test_brightdata_engines.py` used to call `load_dotenv()` at
module scope, so every module collected after it inherited the keys and the
skip guards in unrelated tests stopped skipping. The fix moved that call into
`__main__`; this test keeps it there.
"""

import ast
from pathlib import Path

TESTS_ROOT = Path(__file__).parent


def _module_scope_dotenv_calls(path: Path) -> list[int]:
    """Line numbers of `load_dotenv(...)` calls outside `if __name__ == ...`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))

    guarded: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        # Match ``__name__ == "__main__"`` in either operand order.
        if "__name__" not in ast.dump(node.test):
            continue
        for child in ast.walk(node):
            if hasattr(child, "lineno"):
                guarded.add(child.lineno)

    calls: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        if name == "load_dotenv" and node.lineno not in guarded:
            calls.append(node.lineno)
    return calls


def test_no_test_module_loads_dotenv_at_import_scope():
    offenders = {}
    for path in sorted(TESTS_ROOT.rglob("test_*.py")):
        lines = _module_scope_dotenv_calls(path)
        if lines:
            offenders[str(path.relative_to(TESTS_ROOT))] = lines

    assert not offenders, (
        "these test modules call load_dotenv() at import scope, which leaks "
        f"a developer's .env into every later module: {offenders}"
    )


def test_live_call_modules_are_marked_integration():
    for relative in (
        "websearch/test_debug_google_apis.py",
        "websearch/test_serper_integration.py",
    ):
        source = (TESTS_ROOT / relative).read_text(encoding="utf-8")
        assert "pytestmark = pytest.mark.integration" in source, relative
