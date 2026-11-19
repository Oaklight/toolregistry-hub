# Contributing to toolregistry-hub

## Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Set up pre-commit hooks: `pre-commit install`
5. Make your changes
6. Run `make lint` (or let pre-commit catch issues on commit)
7. Run `make test` to verify nothing is broken
8. Commit and push
9. Open a Pull Request

## Branch Naming

Use descriptive prefixes:

- `feature/xxx` — new functionality
- `fix/xxx` — bug fix
- `refactor/xxx` — code restructuring
- `docs/xxx` — documentation updates
- `test/xxx` — test additions or changes

## Commit Messages

Keep commit messages concise and focused on *why*, not *what*. One logical change per commit.

## Pull Requests

- Keep PRs focused — one feature or fix per PR
- Include a brief description of what changed and why
- Mention any breaking changes explicitly
- Ensure `make lint` passes before submitting
- Merge strategy: rebase

Every PR uses `.github/pull_request_template.md`. The rules below decide how
much review a PR needs and in what order PRs merge.

### Review tiers

Tick one risk tier in the template. When a PR spans tiers, it takes the
highest.

| Tier | Typical change | Review |
| --- | --- | --- |
| Pure move | Code moves with no logic edit | One reviewer checks only that the mechanical proof is credible. CI green plus the proof can merge. |
| Boundary or contract change | Imports, public API, config schema, wire format | One reviewer plus the maintainer. |
| Runtime-behaviour change | Logic that runs differently after the PR | One or two reviewers who read the logic. |
| Security-relevant | Auth, keys, credentials, sanitizing, network exposure | Always reviewed, ideally by someone other than the author's usual reviewer. |

For a pure move, state the mechanical proof in the template: the summary of
`python scripts/dev/check_move.py origin/master --markdown` (when
`scripts/dev/check_move.py` exists) and a passing `ty` hook from
`pre-commit run --all-files`.

### Who reviews what

Reviewer assignment follows the path, not the author's choice. The repository
has no `CODEOWNERS` file, so ask the maintainer (`@Oaklight`) to assign the
reviewer for the area. The areas follow
the repository's `area:*` labels (`.github/labels.yml`):

| Paths under `src/toolregistry_hub/` | Area |
| --- | --- |
| `bash_tool.py`, `bashtool/` | `area:bash`: bash tool. Tags `DESTRUCTIVE`, `PRIVILEGED`: security-relevant tier. |
| `fetch.py` | `area:fetch`: web content fetching and extraction |
| `file_ops.py`, `file_search.py`, `file_reader.py`, `path_info.py`, `gitignore.py` | `area:file-ops`. `file_ops.py` is tagged `DESTRUCTIVE`: security-relevant tier. |
| `server/` | `area:server`: launcher, registry, routing. `server/auth.py` (token auth helpers) is security-relevant. |
| `calculator.py`, `datetime_utils.py`, `weather.py`, `unit_converter.py`, `think_tool.py`, `cron_tool.py` | `area:utilities`. `cron_tool.py` is tagged `PRIVILEGED`: security-relevant tier. |
| `websearch/` | `area:websearch`: web search engines |
| `.github/`, `docker/`, `scripts/`, `Makefile`, `pyproject.toml`, `.pre-commit-config.yaml` | `area:infra`: CI, build, packaging, Docker |

Any other path (`board/`, `academics/`, `data/`): ask the maintainer.

### Series and overlap

Before you open a PR, run the overlap check:

```bash
python scripts/dev/pr_overlap.py            # current branch against origin/master
python scripts/dev/pr_overlap.py --local    # also other local branches
python scripts/dev/pr_overlap.py --fail-on-overlap   # exit 1 on overlap
```

It lists every open PR that touches the same files. It needs the `gh` CLI and
always exits 0 unless you pass `--fail-on-overlap`. When `gh` or git fails, it
says the overlap is unverified and still exits 0.

If a PR overlaps, merge a series one PR at a time and rebase the rest after
each merge.

### Small PRs

- One refactor or one concern per PR.
- Follow-on mechanical edits (formatting, doc touch-ups) go after the PR they
  depend on. Do not open them as independent PRs.

### Requesting review

Request review only after CI is fully green. Do not skip a hook with `SKIP=...`
to get there: the hooks pass on `master`, so a failure is a real diagnostic or
a local environment that does not match CI. If you skipped any hook, name it
and the reason in the template.

## Adding a New Tool

toolregistry-hub uses a registry-based architecture. To add a new tool:

1. Create your tool class under `src/toolregistry_hub/tools/`
2. Register it in `src/toolregistry_hub/server/registry.py`
3. Add any new dependencies as optional extras in `pyproject.toml`
4. Add tests under `tests/`
5. Submit a PR

See existing tools under `src/toolregistry_hub/tools/` for reference implementations.

## AI-Assisted Contributions

Using AI tools (e.g. Claude, Cursor, Copilot) to assist with development is welcome. However:

- **No AI co-author tags in commits.** Do not add `Co-authored-by` lines for AI tools in git commit messages. This keeps the git history clean and readable.
- **Disclose in PR description.** If AI tools were used significantly in your contribution, add a brief note in the PR description (e.g. "AI was used to assist with implementation").
- **You own the code.** Contributors are fully responsible for any AI-generated code they submit — review it, test it, understand it.

## Code Style

- Python code follows `ruff` defaults
- Docstrings use Google style
- Comments and docstrings in English
- Type hints are encouraged

## Checking that a PR is a pure move

A PR that only moves code (splitting a module, relocating methods) should
change no definition. A reviewer cannot see a dropped `@classmethod` in a large
move, so compare the two sides by AST:

```bash
python scripts/dev/check_move.py origin/master          # head defaults to HEAD
python scripts/dev/check_move.py origin/master --markdown   # paste into the PR body
```

The tool compares every function, method, class and class-level assignment of
the changed files by qualified name (and by bare name when a method changes
class), including decorators, arguments, annotations, body and docstring.
Comments and formatting are ignored. Files under `_vendor/` are skipped. It
exits nonzero on a def that is `missing` or `moved-with-diff`. It also fails on
a changed census of `@staticmethod`, `@classmethod` and `@property` decorators
over the changed files (only defs matched between base and head count, so a
split that adds a decorated helper passes, while a decorator dropped from a
moved def fails), and on `undefined-global`: a moved function that reads a
module-level name (a lost `logger` or constant) its new module does not define.
Added `if TYPE_CHECKING:` stubs, a module-level import of a name that used to be
imported inside the function, and `getLogger(__name__)` becoming
`getLogger("<old module name>")` are reported but do not fail.

Record an intended difference with a reason in a file of
`path::qualified.name  reason` lines and pass it with `--allow FILE`. The path
is the repo-relative file of the def; for a def that moved between files, the
head or the base path both work. Use `undefined-global:<head path>::<name>` and
`decorator-census:<decorator>` for those two checks, with the decorator name as
the report prints it in `(allow entry: ...)`, for example
`decorator-census:property` (`decorator-census:@property` is accepted too); the
census counts across all files, so that entry is not tied to a path. A bare
`qualified.name` is rejected, because it would excuse the name in every file.

The `Pure move` workflow runs the same check on pull requests that carry the
`pure-move` label, including when the label is added after the PR was opened.
It reads `.github/pure-move-allow.txt` from the **base branch**, so a PR cannot
exempt itself: land the allow-file entry first, in its own reviewed change.
Apply the label only to a PR you claim is a pure move. A `refactor:` PR that
changes behaviour on purpose does not get the label.

The job is skipped for a PR without the label. A job skipped by its `if:`
counts as success for branch protection, so a required `pure-move` check gates
only the PRs that carry the label.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
