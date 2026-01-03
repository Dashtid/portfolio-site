# Architecture

## Overview

Vue 3 frontend + FastAPI backend with GitHub OAuth authentication.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │────▶│   Fly.io    │────▶│ PostgreSQL  │
│  (Frontend) │     │  (Backend)  │     │  (Database) │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Directory Structure

```
frontend/src/
├── components/    # Reusable UI components
├── views/         # Page components
├── stores/        # Pinia state (auth, portfolio)
├── api/           # HTTP client + CRUD services
├── composables/   # Reusable logic (theme, toast, animations)
└── router/        # Route definitions

backend/app/
├── api/v1/        # REST endpoints
├── models/        # SQLAlchemy ORM
├── schemas/       # Pydantic validation
├── services/      # Business logic (GitHub API)
├── middleware/    # Logging, rate limiting, cache, security
└── core/          # Auth, dependencies
```

## Data Flow

```
User → Vue Component → Pinia Store → Axios → FastAPI → SQLAlchemy → PostgreSQL
```

## Authentication Flow

1. User clicks "Login with GitHub"
2. Backend generates CSRF state, redirects to GitHub
3. GitHub callback validates state, exchanges code for token
4. Backend issues JWT tokens (HTTP-only cookies)
5. Frontend stores auth state in Pinia

## Key Patterns

| Pattern | Description |
|---------|-------------|
| CRUD Service Factory | Generic type-safe API calls (`createCrudService<T>()`) |
| Token Refresh | Request deduplication prevents race conditions |
| Middleware Stack | Security headers, rate limiting, compression, logging |
| Async Database | SQLAlchemy async with connection pooling |
