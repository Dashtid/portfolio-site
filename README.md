# Portfolio Website — dashti.se

[![CI/CD](https://github.com/Dashtid/portfolio-site/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Dashtid/portfolio-site/actions/workflows/ci-cd.yml)
[![CodeQL](https://github.com/Dashtid/portfolio-site/actions/workflows/codeql.yml/badge.svg)](https://github.com/Dashtid/portfolio-site/security/code-scanning)
[![codecov](https://codecov.io/gh/Dashtid/portfolio-site/branch/main/graph/badge.svg)](https://codecov.io/gh/Dashtid/portfolio-site)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Dashtid/portfolio-site/badge)](https://scorecard.dev/viewer/?uri=github.com/Dashtid/portfolio-site)
[![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-lightgrey.svg)](LICENSE)

My personal portfolio site. Vue 3 + FastAPI, deployed to Vercel and Fly.io.
Live at **[dashti.se](https://dashti.se)**.

Source is published as a showcase of the site's architecture and engineering
practice — not as a project intended for reuse or external API consumption.
The site's own [/colophon](https://dashti.se/colophon) is the human-readable
version of this story: what it is built with and how it is secured, with
every claim verifiable against this repository.

## What it does

- Dynamic portfolio content (experience, projects, education) served from an admin-managed backend
- GitHub OAuth sign-in for the admin panel (content CMS, analytics, CV export, OSS dashboard)
- Downloadable publications (thesis PDFs), GitHub stats and an open-source contributions strip rendered live
- Static-site pre-render of every public route for SEO + first-paint speed
- Per-visitor analytics (country-level, no PII stored) with an admin dashboard
- Dark / light theme; a footer build stamp linking every deploy to its exact commit

## Tech stack

| Frontend            | Backend              | Infrastructure       |
| ------------------- | -------------------- | -------------------- |
| Vue 3 + TypeScript  | FastAPI + SQLAlchemy | Vercel (frontend)    |
| vite-ssg (SSG)      | PostgreSQL + Alembic | Fly.io (backend)     |
| Pinia state         | Pydantic v2          | GitHub Actions CI/CD |
| Vitest + Playwright | pytest + ruff + mypy | Codecov + Scorecard  |

## Engineering choices worth showing

A few decisions in the build that aren't obvious from the dependency list:

- **SSG pre-render with hydration handoff.** Every public route is pre-rendered at build time via vite-ssg. Pinia state populated server-side gets serialised into the page HTML and rehydrated on the client — no post-load refetch, no hydration mismatch.
- **Fully hash-locked CSP — no `'unsafe-inline'` anywhere.** `script-src` and `style-src` are `'self'` plus pinned SHA-256 hashes; every hash has a named owner in a unit test that recomputes it from source, the built pages are scanned for styling the policy would not cover, and a CI gate serves the real bundle under the real policy in a browser and fails on any violation. That last gate exists because it once caught a runtime `<style>` injection (the theme switcher's transition guard) that no static scan could see.
- **HTTP-only-cookie auth, no localStorage.** Tokens never touch JavaScript. The refresh endpoint sets cookies and returns `{"refreshed": true}` so an XSS can't lift credentials out of the response body either.
- **HMAC-keyed IP pseudonymisation.** Visitor IPs are hashed with HMAC-SHA256 keyed off `SECRET_KEY` before storage — rainbow-table resistant across the IPv4 space without a second secret to manage.
- **Strict production posture.** `/api/docs`, `/api/redoc` and `/openapi.json` are disabled in production (the API has no third-party consumers); framing denied, MIME sniffing off, HSTS with the domain submitted to the browser preload list.
- **A 2 KB canvas instead of a 122 KB library.** The dark-mode hero animation used to be a three.js starfield; measured against a seeded Canvas2D implementation the visual difference sat below perceptual threshold, so the library went and ~120 KB gzip of JavaScript went with it.
- **CI as a real gate.** Frontend lint + type-check + 610 vitest unit tests + Playwright e2e and visual regression against pixel-pinned baselines. Backend ruff + mypy + 977 pytest tests with an enforced 83% coverage floor. Lighthouse runs every push with assertion-level budgets that fail CI on regressions, and a post-deploy smoke asserts the production security headers — including the hash-locked CSP — after every deploy. Deploy jobs are gated on the quality jobs; no broken commit ships.
- **Supply chain treated as an attack surface.** Every GitHub Action is SHA-pinned (not version-tagged), and a pipeline script re-checks each pin against the version comment beside it. Every Python package installs only if its hash matches the committed lockfile — including pip itself. Trivy is downloaded directly with a checksum check rather than via the (once-compromised) upstream action.

## Run locally

```bash
# Backend — uv manages the environment from pyproject.toml + uv.lock.
# (requirements.txt is the production lockfile: hash-pinned and compiled
# for the Linux deploy image, not for local installs.)
cd backend && uv sync --extra dev
uv run uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

Frontend: `http://localhost:3000` — API: `http://localhost:8000/api/docs`

## Deeper reading

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design
- [docs/API.md](docs/API.md) — endpoint reference
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — production deployment notes
- [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) — DB configuration
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — local dev workflow
- [https://dashti.se/colophon](https://dashti.se/colophon) — the site describing its own security posture

## License

See [LICENSE](LICENSE). All Rights Reserved — code is published for portfolio
viewing only, not licensed for reuse.
