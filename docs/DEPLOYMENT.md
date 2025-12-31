# Production Deployment Guide

This guide covers deploying the Portfolio site to production using Vercel (frontend) and Fly.io (backend).

## Overview

**Architecture**:

- Frontend: Vercel (FREE tier) - Static Vue 3 build with CDN
- Backend: Fly.io - FastAPI container with PostgreSQL
- Domain: dashti.se

**Production URLs**:

- Frontend: <https://dashti.se>
- Backend API: <https://dashti-portfolio-backend.fly.dev>

---

## Prerequisites

1. **Accounts**:

   - [Vercel account](https://vercel.com/signup) (free tier)
   - [Fly.io account](https://fly.io/app/sign-up)
   - GitHub account (for CI/CD)

2. **CLI Tools**:

   ```bash
   # Fly.io CLI
   curl -L https://fly.io/install.sh | sh

   # Vercel CLI (optional - deployment via GitHub is preferred)
   npm i -g vercel
   ```

3. **Domain**:

   - dashti.se configured in Vercel dashboard

---

## Backend Deployment (Fly.io)

### Backend Configuration

The backend is configured via `backend/fly.toml`:

| Setting  | Value                      |
| -------- | -------------------------- |
| App name | `dashti-portfolio-backend` |
| Region   | `arn` (Stockholm)          |
| Memory   | 1 GB                       |
| CPU      | 1 shared                   |
| Port     | 8000                       |

### Step 1: Login to Fly.io

```bash
fly auth login
```

### Step 2: Set Environment Variables

```bash
cd backend

# Required secrets
fly secrets set SECRET_KEY="your-secret-key"
fly secrets set GITHUB_CLIENT_ID="your-github-oauth-client-id"
fly secrets set GITHUB_CLIENT_SECRET="your-github-oauth-client-secret"
fly secrets set SENTRY_DSN="your-sentry-dsn"

# Database (if using external PostgreSQL)
fly secrets set DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

### Step 3: Deploy

```bash
fly deploy
```

### Step 4: Verify

```bash
# Check app status
fly status

# View logs
fly logs

# Health check
curl https://dashti-portfolio-backend.fly.dev/api/v1/health
```

### Scaling

```bash
# Scale machines
fly scale count 2

# Scale memory
fly scale memory 2048
```

---

## Frontend Deployment (Vercel)

### Frontend Configuration

The frontend is configured via `frontend/vercel.json`:

- Build command: `npm run build`
- Output directory: `dist`
- Framework: Vite

### Automatic Deployment

Frontend deploys automatically via GitHub Actions on push to `main`/`master`.

### Manual Deployment

```bash
cd frontend
vercel --prod
```

### Environment Variables

Set in Vercel dashboard under Project Settings > Environment Variables:

| Variable          | Value                                      |
| ----------------- | ------------------------------------------ |
| `VITE_API_URL`    | `https://dashti-portfolio-backend.fly.dev` |
| `VITE_SENTRY_DSN` | Your Sentry DSN                            |

### Security Headers

The following headers are configured in `vercel.json`:

- Content-Security-Policy (strict)
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options
- X-Frame-Options
- Permissions-Policy

### Caching Strategy

| Asset Type   | Cache Duration                     |
| ------------ | ---------------------------------- |
| `/assets/*`  | 1 year (immutable)                 |
| `/images/*`  | 24 hours + stale-while-revalidate  |
| `/sw.js`     | No cache (must-revalidate)         |

---

## CI/CD Pipeline

GitHub Actions workflows handle:

1. **Frontend**: Lint, test, build, deploy to Vercel
2. **Backend**: Lint, test, deploy to Fly.io
3. **E2E Tests**: Playwright tests on Chromium + Firefox

Workflows are in `.github/workflows/`:

- `ci-cd.yml` - Main test pipeline
- `deploy-frontend.yml` - Vercel deployment
- `deploy-backend.yml` - Fly.io deployment

---

## Monitoring

### Health Checks

- Backend: `GET /api/v1/health` (every 30s)
- Frontend: Vercel edge health checks

### Error Tracking

Sentry is configured for both frontend and backend:

- Captures exceptions automatically
- Performance monitoring enabled
- PII disabled

### Logs

```bash
# Backend logs
fly logs -a dashti-portfolio-backend

# Real-time
fly logs -a dashti-portfolio-backend --follow
```

---

## Troubleshooting

### Backend Issues

```bash
# SSH into container
fly ssh console

# Check database connection
fly postgres connect -a dashti-portfolio-backend-db

# Restart app
fly apps restart dashti-portfolio-backend
```

### Frontend Issues

```bash
# Check Vercel deployment status
vercel ls

# View build logs
vercel logs <deployment-url>
```

### Common Issues

| Issue           | Solution                                    |
| --------------- | ------------------------------------------- |
| 502 Bad Gateway | Check backend health, restart if needed     |
| CORS errors     | Verify `CORS_ORIGINS` in backend config     |
| OAuth failure   | Check `GITHUB_CLIENT_ID` and callback URL   |

---

Last Updated: 2025-12-31
