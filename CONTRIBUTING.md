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
`pre-commit run --all-files`. Give the equivalent evidence by hand only where a
tool cannot run.

### Who reviews what

Reviewer assignment follows the path, not the author's choice. The repository
has no `CODEOWNERS` file, so ask the maintainer (`@Oaklight`) to assign the
reviewer for the area. The areas follow the repository's `area:*` labels
(`.github/labels.yml`). Every path below exists in the tree
(`git ls-files`); the security-relevant rows name the module that holds the
behaviour.

| Paths under `src/toolregistry_hub/` | Area |
| --- | --- |
| `url_policy.py`, `fetch.py` | **Security-relevant**, outbound network access. `url_policy.py` decides which URLs `fetch` may reach (scheme check; the address decision is in `toolregistry.netpolicy`); `fetch.py` applies it. Label `area:fetch`. |
| `server/admin_cli.py` | **Security-relevant**, authentication. Resolves the admin panel's bearer token and refuses a non-loopback host without one. Label `area:server`. |
| `bash_tool.py`, `bashtool/` | **Security-relevant**, `area:bash`. `BashTool` is tagged `DESTRUCTIVE` and `PRIVILEGED` in `bash_tool.py`. `bashtool/` is a git submodule (`Oaklight/bashtool`): a PR here changes the pinned commit. |
| `file_ops.py` | **Security-relevant**, `area:file-ops`. Tagged `DESTRUCTIVE` in the module. |
| `cron_tool.py` | **Security-relevant**, `area:utilities`. Tagged `PRIVILEGED` in the module. |
| `file_search.py`, `file_reader.py`, `path_info.py`, `gitignore.py` | `area:file-ops` |
| `server/` (other files: `cli.py`, `registry.py`, `app.py`, `banner.py`) | `area:server`: launcher, registry, app |
| `websearch/`, `utils/api_key_parser.py` | `area:websearch`: search engines and the API key rotation they use |
| `calculator.py`, `datetime_utils.py`, `weather.py`, `unit_converter.py`, `think_tool.py` | `area:utilities` |
| `_vendor/` | Never edit by hand. These modules are vendored from zerodep with hashes in `_vendor/zerodep.lock.json`: re-vendor from upstream and review the re-vendor diff. |
| `.github/`, `docker/`, `scripts/`, `Makefile`, `pyproject.toml`, `.pre-commit-config.yaml` | `area:infra`: CI, build, packaging, Docker |

Any other path (`board/`, `academics/`, `data/`, `version_check.py`,
`_metadata.py`, `utils/` other than `api_key_parser.py`) has no `area:*`
label: ask the maintainer. `board/tools.py` carries `DESTRUCTIVE` tags, so
treat a change there as at least runtime-behaviour.

### Series and overlap

Before you open a PR, run the overlap check:

```bash
python scripts/dev/pr_overlap.py            # current branch against the remote default branch
python scripts/dev/pr_overlap.py --local    # also other local branches
python scripts/dev/pr_overlap.py --fail-on-overlap   # gate: 1 overlap, 2 unverified
```

It lists every open PR that touches the same files, and leaves out the PR of
the branch itself (matched by branch name, by head commit, or by
`$GITHUB_HEAD_REF`), so `--head HEAD` or a SHA works in a detached checkout. The
base defaults to `origin/HEAD`, then `origin/main`, then `origin/master`. The
tool needs the `gh` CLI and exits 0 unless you pass `--fail-on-overlap`. That
gate exits 1 on overlap and 2 when the check could not complete (`gh` missing or
failing, bad output, no base branch found, or 200 open PRs so the list may be
truncated); a gate does not pass on a check that did not finish.

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

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
