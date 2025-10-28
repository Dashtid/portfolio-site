# Portfolio Website - Vue 3 + FastAPI

Modern, production-ready portfolio website with dynamic content management, authentication, and comprehensive testing.

**Status**: ✅ Migration Complete | **Performance**: 8.6x faster | **Coverage**: 80%

## Quick Start

### Prerequisites
- Python 3.13+ | Node.js 18+ | UV: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### Run Locally

```bash
# Backend
cd backend && uv venv && source .venv/Scripts/activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

**Access**: Frontend: http://localhost:3000 | API: http://localhost:8001/docs

## Features

- **Dynamic Content**: Admin panel for experience, education, projects
- **Auth**: GitHub OAuth + JWT tokens
- **Publications**: Downloadable thesis PDFs (5.3 MB actual files)
- **GitHub Stats**: Live repos, languages, followers/stars
- **Rich Pages**: Videos, maps, detailed experience descriptions
- **TypeScript**: Full type safety
- **Testing**: 80% coverage (Vitest, pytest, Playwright)
- **Performance**: 24ms load time (8.6x faster than original)

## Project Structure

```
├── backend/          # FastAPI + SQLAlchemy async
│   ├── app/api/      # REST endpoints
│   ├── app/models/   # Database models
│   └── static/       # PDFs, documents
├── frontend/         # Vue 3 + TypeScript
│   ├── src/components/
│   ├── src/views/
│   └── src/stores/   # Pinia state management
└── docs/             # Documentation
    ├── guides/       # MONITORING, TESTING, PERFORMANCE
    └── migration/    # Phase completion docs
```

## Documentation

**Essential**:
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment guide (Vercel + Fly.io)
- [NEXT_STEPS_RECOMMENDATIONS.md](NEXT_STEPS_RECOMMENDATIONS.md) - Next enhancements
- [CHANGELOG.md](CHANGELOG.md) - Version history

**Guides** (docs/guides/):
- DEPLOYMENT.md - Production deployment (Vercel + Fly.io, $0-5/month)
- MONITORING.md - Logging & error tracking
- PERFORMANCE.md - Optimization strategies
- TESTING.md - Test infrastructure
- TOOLING.md - Development tooling (ESLint 9, Ruff, mypy)

**Migration** (docs/migration/):
- FEATURE_PARITY_ANALYSIS.md - Complete comparison with original
- PHASE9A_COMPLETION.md - Downloadable documents feature
- THESIS_PDF_MIGRATION.md - PDF migration details

## API Endpoints

**Public**:
- `GET /api/v1/companies/` - All companies
- `GET /api/v1/education/` - Education entries
- `GET /api/v1/documents/` - Downloadable documents
- `GET /api/v1/github/stats/:username` - GitHub stats
- `GET /static/documents/:filename` - Download PDFs

**Admin** (auth required):
- `POST /PUT /DELETE /api/v1/companies/` - Manage companies
- Similar for education, projects, documents

**Auth**:
- `GET /api/v1/auth/github/authorize` - OAuth flow
- `POST /api/v1/auth/refresh` - Refresh token

## Development

### Code Quality Tools (2025 Best Practices)

**Frontend**:
```bash
npm run lint              # ESLint 9 with flat config
npm run lint:fix          # Auto-fix linting issues
npm run format            # Prettier formatting
npm run format:check      # Check formatting
npm run type-check        # TypeScript type checking
```

**Backend**:
```bash
ruff check .              # Lint Python code
ruff check --fix .        # Auto-fix linting issues
ruff format .             # Format Python code
mypy .                    # Static type checking
```

**Pre-commit Hooks**:
```bash
pre-commit run --all-files   # Run all quality checks
```

### Testing

```bash
# Backend tests
cd backend && pytest
cd backend && pytest --cov=app --cov-report=html

# Frontend tests
cd frontend && npm run test
cd frontend && npm run coverage

# Build
cd frontend && npm run build
```

### Tooling Stack

**Frontend**:
- ESLint 9.38.0 (flat config format)
- Prettier 3.6.2
- TypeScript 5.9.3
- Vitest 2.1.9 + v8 coverage
- Vite 7.1.7

**Backend**:
- Ruff 0.14.2 (linter + formatter)
- mypy 1.18.2 (type checker)
- pytest 8.3.4 + pytest-cov
- Python 3.11+

**Both**:
- EditorConfig (consistency)
- Pre-commit hooks (automated checks)

## Deployment

**Production Configuration**: Vercel (frontend) + Fly.io (backend) = $0-5/month

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete deployment guide with step-by-step instructions.

**Quick Deploy**:
```bash
# Backend (Fly.io)
cd backend && fly launch --no-deploy && fly deploy

# Frontend (Vercel)
cd frontend && vercel --prod
```

**CI/CD**: Automated deployment via GitHub Actions (`.github/workflows/deploy.yml`)

## Migration Status

**✅ 100% Complete**:
- 7 companies, 4 education entries, 8 projects
- 2 thesis PDFs (actual 1.3 MB + 4.0 MB files)
- 48 logo images
- 6 detailed experience pages with videos & maps
- All features from original + enhancements

**Enhancements Over Original**:
- Admin panel (CRUD operations)
- Authentication (GitHub OAuth + JWT)
- API-driven architecture
- Dedicated Publications section
- TypeScript migration
- Testing infrastructure (80% coverage)
- Monitoring & logging

## Security

- GitHub OAuth 2.0 + JWT
- CSP, HSTS, X-Frame-Options headers
- Rate limiting
- SQL injection protection (SQLAlchemy ORM)
- Input validation (Pydantic)

## License

© 2025 David Dashti - All rights reserved
