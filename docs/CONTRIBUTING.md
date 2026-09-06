# Contributing

This repository is published as a portfolio showcase rather than as a
project soliciting outside contributions. The notes below describe how
the codebase is set up locally for the author's own reference.

## Development Setup

```bash
# Backend — uv drives the environment from pyproject.toml + uv.lock.
# (requirements.txt is the hash-pinned PRODUCTION lockfile, compiled for
# the Linux deploy image — don't install from it locally.)
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Code Style

- **Python**: ruff for lint + format (replaces black), mypy for types
- **TypeScript**: ESLint + Prettier, vue-tsc for types
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, …)

## Testing

```bash
# Backend (977 tests, 83% coverage floor)
cd backend && uv run pytest

# Frontend unit (610 tests)
cd frontend && npm test

# Frontend e2e — run via Docker for parity with CI, which runs the
# chromium project (the harness image pins the browser build the visual
# baselines were generated with)
cd frontend && npm run test:e2e:visual:docker

# Enforced-CSP check (serves the built dist under the real policy)
cd frontend && npm run build:ssg && npm run verify:csp
```

## Pre-commit Hooks

`.pre-commit-config.yaml` carries the shared hook set (prettier, eslint,
ruff check + format, mypy, markdownlint, actionlint, shellcheck, gitleaks,
detect-private-key, conventional-commit message check, and assorted
hygiene checks). Install once with:

```bash
pre-commit install
```

After that, every `git commit` runs the matching hooks and aborts if any
file is modified — re-stage and commit again. The same hook set runs
against the full tree in CI (`.github/workflows/pre-commit.yml`), so a
skipped local hook still gets caught.
