# Portfolio Website — dashti.se

[![CI/CD](https://github.com/Dashtid/portfolio-site/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Dashtid/portfolio-site/actions/workflows/ci-cd.yml)
[![CodeQL](https://github.com/Dashtid/portfolio-site/actions/workflows/codeql.yml/badge.svg)](https://github.com/Dashtid/portfolio-site/security/code-scanning)
[![codecov](https://codecov.io/gh/Dashtid/portfolio-site/branch/main/graph/badge.svg)](https://codecov.io/gh/Dashtid/portfolio-site)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Dashtid/portfolio-site/badge)](https://scorecard.dev/viewer/?uri=github.com/Dashtid/portfolio-site)
[![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-lightgrey.svg)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/Dashtid/portfolio-site)](https://github.com/Dashtid/portfolio-site/commits/main)

My personal portfolio site, built end-to-end as a playground for modern web
architecture. Live at **[dashti.se](https://dashti.se)**.

This repo is a showcase of how the site is built — not a project intended
for reuse or external API consumption.

## What it does

- Dynamic portfolio content (experience, projects, education) served from an admin-managed backend
- GitHub OAuth sign-in for the admin panel
- Downloadable publications (thesis PDFs) and GitHub stats rendered live
- Static-site pre-render of every public route for SEO + first-paint speed
- Per-visitor analytics (country-level, no PII stored) with an admin dashboard
- Dark / light theme

## Tech stack

| Frontend            | Backend              | Infrastructure        |
| ------------------- | -------------------- | --------------------- |
| Vue 3 + TypeScript  | FastAPI + SQLAlchemy | Vercel (frontend)     |
| vite-ssg (SSG)      | SQLite + Alembic     | Fly.io (backend)      |
| Pinia state         | Pydantic v2          | GitHub Actions CI/CD  |
| Vitest + Playwright | pytest + ruff + mypy | Codecov + Scorecard   |

## Engineering choices worth showing

A few decisions in the build that aren't obvious from the dependency list:

- **SSG pre-render with hydration handoff.** Every public route is pre-rendered at build time via vite-ssg. Pinia state populated server-side gets serialised into the page HTML and rehydrated on the client — no post-load refetch, no hydration mismatch.
- **HTTP-only-cookie auth, no localStorage.** Tokens never touch JavaScript. The refresh endpoint sets cookies and returns `{"refreshed": true}` so an XSS can't lift credentials out of the response body either.
- **HMAC-keyed IP pseudonymisation.** Visitor IPs are hashed with HMAC-SHA256 keyed off `SECRET_KEY` before storage — rainbow-table resistant across the IPv4 space without a second secret to manage.
- **Strict production posture.** Locked-down CSP; `/api/docs` / `/api/redoc` / `/openapi.json` all disabled in production (the API has no third-party consumers); CSP `script-src` is `'self'` only.
- **Tree-shaken three.js for the hero animation.** Switching from `import * as THREE` to named imports let Rollup tree-shake the chunk by 32% (732KB → 496KB raw; 181KB → 120KB gzip; −61KB on the home page). Dynamic namespace access can't be tree-shaken; named imports can.
- **CI as a real gate.** Frontend lint + type-check + 617 vitest unit tests + 5-browser Playwright e2e. Backend ruff + 667 pytest tests with an enforced 83% coverage floor (currently 86%). Lighthouse runs every push against assertion-level budgets that fail CI on regressions. Deploy jobs gated on quality jobs — no broken commits ship.
- **SHA-pinned actions, checksum-verified Trivy.** All GitHub Action references are SHA-pinned (not version tags) after the March 2025 `tj-actions/changed-files` supply-chain incident; Trivy is downloaded directly with a checksum check rather than via the (also-compromised) `aquasecurity/trivy-action`.

## Run locally

```bash
# Backend
cd backend && uv venv && source .venv/Scripts/activate
uv pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

Frontend: `http://localhost:5173` — API: `http://localhost:8000/api/docs`

## Deeper reading

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design
- [docs/API.md](docs/API.md) — endpoint reference
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — production deployment notes
- [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) — DB configuration
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — local dev workflow
- [CHANGELOG.md](CHANGELOG.md) — version history
- [BACKLOG.md](BACKLOG.md) — tracked work items

## License

See [LICENSE](LICENSE). All Rights Reserved — code is published for portfolio
viewing only, not licensed for reuse.
