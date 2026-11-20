<!-- Read the "Pull Requests" section of CONTRIBUTING.md first. -->

## What and why

<!-- One concern per PR. Link the issue. -->

## Risk tier (tick one)

- [ ] Pure move: code moves, no logic edit (a mechanical check proves it)
- [ ] Boundary or contract change: imports, public API, config schema, wire format
- [ ] Runtime-behaviour change: logic that runs differently after this PR
- [ ] Security-relevant: auth, keys, credentials, sanitizing, network exposure

## Verification

- [ ] `pre-commit run --all-files` passes (ruff, ty, complexipy). Result:
- [ ] `python -m pytest tests/ -v --tb=short` passes (the command CI runs). Result:
- [ ] Pure move only: summary of `python scripts/dev/check_move.py origin/master --markdown`:
- [ ] Overlap check done: `python scripts/dev/pr_overlap.py` shows no open PR on the same files (the tool leaves out this PR itself), or the merge order is stated here:
- [ ] CI is fully green before review is requested

## Changelog

- [ ] Changelog-worthy change: `[Unreleased]` entry added to `docs_en/docs/changelog.md` and `docs_zh/docs/changelog.md` (separate branches, one commit each), or "not applicable":

## AI disclosure

- [ ] AI tools were used for: <!-- describe, or write "none" -->. No `Co-authored-by` AI tags are in the commits.

## Skipped hooks

<!-- If a hook was skipped (for example a CI-only check you could not run locally), name it and say why. Write "none" otherwise. -->
