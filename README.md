# Portfolio Website

Personal portfolio built with Vue 3 + FastAPI.

[![CI/CD](https://github.com/daviddashti/portfolio-site/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/daviddashti/portfolio-site/actions)
[![CodeQL](https://github.com/daviddashti/portfolio-site/actions/workflows/codeql.yml/badge.svg)](https://github.com/daviddashti/portfolio-site/security/code-scanning)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](backend/)

**Live**: [dashti.se](https://dashti.se) | **API**: [dashti-portfolio-backend.fly.dev](https://dashti-portfolio-backend.fly.dev/api/v1/)

## Quick Start

```bash
# Backend
cd backend && uv venv && source .venv/Scripts/activate
uv pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

**Local**: Frontend `http://localhost:5173` | API `http://localhost:8000/docs`

## Tech Stack

| Frontend             | Backend              | Infrastructure       |
| -------------------- | -------------------- | -------------------- |
| Vue 3 + TypeScript   | FastAPI + SQLAlchemy | Vercel (frontend)    |
| Pinia state          | PostgreSQL           | Fly.io (backend)     |
| Vitest + Playwright  | pytest + mypy        | GitHub Actions CI/CD |

## Features

- Dynamic content management with admin panel
- GitHub OAuth authentication
- Downloadable publications (thesis PDFs)
- Live GitHub stats integration
- Dark/light theme support

## Development

```bash
npm run lint && npm run test    # Frontend
ruff check . && pytest          # Backend
pre-commit run --all-files      # All quality checks
```

## Docs

- [CHANGELOG.md](CHANGELOG.md) - Version history
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [docs/API.md](docs/API.md) - API reference
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) - Development guide
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment
- [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) - Database configuration

## License

Copyright 2025 David Dashti
