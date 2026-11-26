# Architecture

## Overview

Vue 3 frontend + FastAPI backend with GitHub OAuth authentication.

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │────▶│   Fly.io    │────▶│ PostgreSQL  │
│  (vite-ssg) │     │  (FastAPI)  │     │ (Fly Postgres)
└─────────────┘     └─────────────┘     └─────────────┘
```

The frontend is statically pre-rendered at build time via vite-ssg —
every public route ships as HTML for SEO and first-paint speed, then
hydrates into a full Vue app on the client.

## Directory Structure

```text
frontend/src/
├── components/    # Reusable UI components
├── views/         # Page components (pre-rendered by vite-ssg)
├── stores/        # Pinia state (auth, portfolio, experience-detail)
├── api/           # axios client + CRUD service factory
├── composables/   # Reusable logic (theme, toast, animations)
├── utils/         # Markdown, logger, storage, type guards
└── router/        # Route definitions + scroll behaviour

backend/app/
├── api/v1/        # REST endpoints (companies, education, projects, skills,
│                  # documents, github, analytics, auth, health)
├── models/        # SQLAlchemy ORM
├── schemas/       # Pydantic v2 validation
├── services/      # External integrations (GitHub API)
├── middleware/    # Logging, rate limiting, cache, security headers, CSP
├── core/          # Auth, dependencies, security helpers
└── utils/         # Logger, IP hashing, daily visitor key
```

## Data Flow

```text
SSG build:  build script → /api/v1/companies → vite-ssg → pre-rendered HTML

Runtime:    User → Vue route → Pinia store (hydrated from inline JSON) →
            axios → FastAPI → SQLAlchemy → PostgreSQL
```

During SSG, Pinia state populated server-side is serialised into the page
HTML and rehydrated on the client — components see the fetched data
immediately, no post-load refetch, no hydration mismatch.

## Authentication Flow

1. User clicks "Login with GitHub" on `/admin/login`
2. Backend generates a single-use CSRF state (5-minute TTL, database-backed), binds it to the browser with an HttpOnly cookie that also holds a PKCE code verifier, and redirects to GitHub with the verifier's S256 challenge
3. GitHub callback validates the state, exchanges the code for a GitHub access token, fetches the user profile
4. Backend issues a JWT access + refresh token pair and sets them as HTTP-only `secure` `samesite=lax` cookies
5. Frontend Pinia auth store mirrors **only** the user object (`{id, username, name, email, avatar_url}`); tokens never reach JavaScript
6. On 401, the axios response interceptor calls `/api/v1/auth/refresh` (cookies travel automatically); the backend rotates both cookies and returns a token-free body. The original request is retried transparently

## Key Patterns

| Pattern | Description |
|---------|-------------|
| Static-site generation | vite-ssg pre-renders public routes; Pinia state hydrated via inline JSON |
| CRUD Service Factory | Generic, type-safe API calls (`createCrudService<T>()`) |
| Cookie-only auth | HTTP-only cookies for tokens; refresh endpoint returns no body tokens |
| Token-refresh dedup | A subscriber queue funnels concurrent 401s through a single refresh call |
| Visitor pseudonymisation | analytics rows carry a daily visitor key (HMAC under an in-memory salt replaced every UTC day), never an address; log lines carry a keyed HMAC-SHA256 digest of the address |
| Middleware stack | Security headers, environment-conditional CSP, rate limiting, compression, logging |
| Async database | SQLAlchemy async with connection pooling; Alembic for migrations |
| SHA-pinned actions | All GitHub Actions referenced by full commit SHA, not version tag |
