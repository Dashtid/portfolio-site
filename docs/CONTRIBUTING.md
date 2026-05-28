# Contributing

This repository is published as a portfolio showcase rather than as a
project soliciting outside contributions. The notes below describe how
the codebase is set up locally for the author's own reference.

## Development Setup

```bash
# Backend
cd backend
uv venv && source .venv/Scripts/activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Code Style

- **Python**: ruff for lint + format (replaces black)
- **TypeScript**: ESLint + Prettier
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, …)

## Testing

```bash
# Backend (667 tests, 86% coverage floor)
cd backend && pytest

# Frontend unit (617 tests)
cd frontend && npm test

# Frontend e2e (Playwright, 5 browser projects — run via Docker for parity with CI)
cd frontend && npm run test:e2e:docker
```

## Pre-commit Hooks

`pre-commit` is configured in `.pre-commit-config.yaml` (trailing whitespace,
end-of-file fixer, prettier, eslint, ruff, mypy). Install hooks once with:

```bash
pre-commit install
```

After that, every `git commit` runs the matching hooks and aborts if any
file is modified — re-stage and commit again. Run all hooks against the
full tree explicitly with `pre-commit run --all-files`.
