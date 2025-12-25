# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
