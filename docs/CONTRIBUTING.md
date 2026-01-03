# Contributing

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

- **Python**: Ruff for linting, Black formatting
- **TypeScript**: ESLint + Prettier
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, etc.)

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test

# E2E
cd frontend && npm run test:e2e
```

## Pull Requests

1. Create feature branch from `main`
2. Make changes with tests
3. Run `pre-commit run --all-files`
4. Open PR with clear description
