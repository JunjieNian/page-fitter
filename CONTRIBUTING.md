# Contributing to page-fitter

Thanks for your interest in contributing! This document covers the basics.

## Development setup

```bash
git clone https://github.com/JunjieNian/page-fitter.git
cd page-fitter
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

You also need a working LaTeX distribution (`pdflatex` or `latexmk`) to run
the full pipeline. The unit tests use pre-built fixture data and do **not**
require LaTeX.

## Running tests

```bash
pytest
```

Tests live in `tests/` and use the fixture at `tests/fixture/` (a minimal
LaTeX project with pre-computed pipeline outputs).

## Coding style

- Python 3.9+ (no walrus operator in hot paths for readability).
- Format & lint with [Ruff](https://docs.astral.sh/ruff/):
  ```bash
  ruff check scripts/ tests/
  ruff format scripts/ tests/
  ```
- Each script under `scripts/` is both CLI-runnable (`python script.py --help`)
  and importable. Keep that dual contract.
- Heavy dependencies (`fitz`, `pylatexenc`) are imported **lazily** so
  `--help` works without them installed.

## Architecture overview

The pipeline has 4 layers — see `references/architecture.md` for the full
picture:

1. **Compile state** (`scripts/compile_state/`) — compile, parse PDF/SyncTeX/log
2. **Candidates** (`scripts/candidates/`) — enumerate editable spans from LaTeX AST
3. **Layout** (`scripts/layout/`) — estimate line-delta and float risk
4. **Scoring** (`scripts/scoring/`) — rank by boundary leverage and semantic cost

All inter-layer data flows as JSON. Schemas are specified in
`references/output-schema.md` — deviations are bugs.

## Pull requests

1. Fork the repo and create a feature branch from `main`.
2. Keep PRs focused — one logical change per PR.
3. Add or update tests for any new logic.
4. Make sure `pytest` and `ruff check` pass before opening the PR.
5. Write a clear PR description explaining *why*, not just *what*.

## Proposing changes to the scoring formula

The scoring formula (`references/boundary-scoring.md`) is the project's core
heuristic. If you want to change coefficients or add new terms:

- Open an issue first with your reasoning and evidence.
- Include before/after comparisons on at least one real paper.
- Changes to the formula need sign-off from a maintainer before merge.

## Reporting issues

- Bug reports: include the LaTeX compiler version, Python version, and the
  error message / traceback.
- Feature requests: describe the use case, not just the desired solution.
