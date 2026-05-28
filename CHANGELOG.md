# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Security

- **Cookie-only authentication**: tokens removed from Pinia state, localStorage, and axios default headers; `/auth/refresh` now sets HTTP-only cookies and returns a token-free body so XSS cannot exfiltrate credentials
- **HMAC-keyed IP pseudonymisation**: replaced unsalted SHA-256 IP hash in analytics with HMAC-SHA256 keyed off `SECRET_KEY` (rainbow-table resistant)
- **Strict production posture**: `/api/docs`, `/api/redoc`, and `/openapi.json` disabled in production; backend CSP drops `cdn.jsdelivr.net` (no longer needed)
- `SECURITY.md` added with vulnerability reporting policy
- 25 known CVEs patched (5 backend + 7 frontend Dependabot PRs merged; remaining 5 transitives gated behind `@lhci/cli`, dev-only)

### Changed

- **CI/CD consolidated**: standalone `deploy-frontend.yml` / `deploy-backend.yml` workflows inlined as `deploy-frontend` + `deploy-backend` jobs in `ci-cd.yml`, gated on the matching quality jobs
- **Lighthouse budgets promoted to errors**: `resource-summary:script:size` and `resource-summary:total:size` warns → errors with realistic ceilings; `categories:best-practices` warn → error
- **Workflow permissions tightened**: workflow-level default reduced to `contents: read`; jobs that need PR-comment write raise their own
- **Backend Docker image SHA-pinned**: `python:3.13-slim` → `python:3.13-slim@sha256:7ba5f5…` for reproducible builds
- README rewritten as a portfolio showcase rather than an OSS quick-start
- LICENSE added as All Rights Reserved
- `actions/dependency-review-action` bumped v4 → v5.0.0 (Node 24)

### Added

- **Codecov uploads** for both frontend (lcov) and backend (coverage.xml) with `flags:` to separate dashboards
- **OpenSSF Scorecard** workflow — weekly + on push to main, published badge
- Three.js tree-shake via static named imports (−61KB gzip on the home page)

### Fixed

- Backend `SECRET_KEY` env var added to `ci-cd.yml` `backend-quality` (latent gap from earlier workflow consolidation)
- Pre-existing CI failures resolved: eslint global `getComputedStyle` (switched to `globals` package) and Trivy 0.62 (404, bumped to 0.70 with checksum verification)

### Tested

- Backend: 667 tests passing, 85.98% coverage (83% floor enforced)
- Frontend: 617 unit tests passing, real Codecov ingestion on every push

## [1.1.0] - 2025-12-25

Technical debt reduction and infrastructure improvements.

### Changed

- **OAuth State Storage**: Migrated from in-memory dict to database-backed storage for multi-instance deployments (Fly.io, Kubernetes)
- **Pydantic Schemas**: Migrated all schemas from deprecated `class Config` to v2 `model_config` pattern
- **Frontend Types**: Consolidated types to use Zod schema inference as single source of truth
- **Logging**: Replaced all `print()` statements with structured logger in init_db.py and seed_data.py
- **Configuration**: Changed DEBUG default to False (must explicitly enable in development)
- **Service Worker**: Added debug mode toggle (disabled by default for cleaner production logs)
- **Storage Keys**: Consolidated to single source of truth in storage.ts

### Added

- Background task for periodic OAuth state cleanup (every 5 minutes)
- Input validation for error endpoint (max lengths, context dict size limits)
- package-lock.json for reproducible builds and security auditing

### Fixed

- ProjectCard component type alignment with backend Project schema
- Timezone-aware datetime comparison in OAuth state expiration
- Test suite compatibility with database-backed OAuth state
- GitHub redirect URI port mismatch in .env.example (8001 -> 8000)
- Added missing VITE_SENTRY_DSN to frontend .env.example

### Security

- OAuth states now persisted securely in database with automatic expiration cleanup
- States are single-use (consumed on callback) preventing replay attacks
- Database table drop requires ALLOW_DB_DROP=true environment variable
- Error endpoint validates request payload sizes to prevent DoS

### Tested

- Backend: 500 tests passing (79.97% coverage)
- Frontend: 625 tests passing
- All npm packages audited (0 vulnerabilities)

## [1.0.0] - 2025-12-14

Production-ready release with Vue 3 + FastAPI architecture.

### Added
- Vue 3 + TypeScript frontend with Pinia state management
- FastAPI backend with SQLAlchemy async ORM
- GitHub OAuth 2.0 authentication with JWT tokens
- Admin panel for CRUD operations on experience, education, projects
- Publications section with downloadable thesis PDFs
- GitHub stats integration (repos, languages, followers)
- Detailed experience pages with videos and maps
- PWA support with service worker
- E2E testing with Playwright
- Unit testing with Vitest (frontend) and pytest (backend)
- Security headers (CSP, HSTS, X-Frame-Options)
- Rate limiting on API endpoints

### Infrastructure
- Frontend deployed on Vercel
- Backend deployed on Fly.io with PostgreSQL
- CI/CD via GitHub Actions
- Pre-commit hooks for code quality

### Repository Cleanup
- Removed unused Docker infrastructure (docker-compose, nginx)
- Removed duplicate thesis PDFs from frontend
- Removed platform-specific visual test snapshots
- Consolidated documentation

## [0.9.0] - 2025-12-11

### Added
- Testing infrastructure improvements
- Dark mode styling fixes
- Navigation improvements
- Data-testid attributes for E2E tests

### Fixed
- TypeScript and ESLint errors
- Prettier formatting across components
- NavBar test alignment with navigation items

## [0.8.0] - 2025-12-10

### Added
- Monitoring and analytics integration
- Comprehensive E2E testing setup

### Security
- Security improvements across frontend and backend
- Input validation hardening

## [0.7.0] - 2025-12-09

### Changed
- UI redesign: removed GitHub stats section
- Redesigned About section
- Removed contact form

### Added
- Profile photo to About section
- Projects grid restoration

## [0.6.0] - 2025-12-06

### Added
- Profile photo feature
- BackToTop button on company detail pages
- Comprehensive UI/UX improvements

### Fixed
- Multiple UI/UX issues
- PyJWT dependency for authentication
- slowapi dependency for rate limiting

## [0.5.0] - 2025-12-05

### Added
- Security hardening and code quality improvements

### Fixed
- TypeScript errors and Python linting issues
- ESLint warnings and CodeQL action
- Mobile accessibility and theme toggle visibility

### Changed
- Synced local data with dashti.se production content
- Updated company names to match production database

## [0.4.0] - 2025-12-04

### Fixed
- ESLint configuration with browser globals
- Prettier formatting across all files
- Vue attribute ordering per ESLint rules

## Initial Migration - 2025-10-28

### Migrated
- 7 companies with detailed experience pages
- 4 education entries
- 8 projects
- 2 thesis PDFs (Bachelor + Master)
- 48 logo images
- All features from original static site
