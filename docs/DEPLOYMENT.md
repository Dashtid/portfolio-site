# Production Deployment Guide

This guide covers deploying the Portfolio Migration project to production using Vercel (frontend) and Fly.io (backend).

## Overview

**Architecture**:
- Frontend: Vercel (FREE tier) - Static Vue 3 build with CDN
- Backend: Fly.io ($5/month) - FastAPI container with PostgreSQL
- Total Cost: $0-5/month

**URLs**:
- Frontend Production: https://dashti.se (custom domain) or https://your-project.vercel.app
- Backend Production: https://dashti-portfolio-backend.fly.dev
- Old Site: https://dashti.se (Azure Static Web Apps - will be replaced)

---

## Prerequisites

1. **Accounts**:
   - [Vercel account](https://vercel.com/signup) (free)
   - [Fly.io account](https://fly.io/app/sign-up) (credit card required for $5/month plan)
   - GitHub account (for CI/CD)

2. **CLI Tools**:
   ```bash
   # Install Fly.io CLI (Windows PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

   # Install Vercel CLI (optional, for manual deployments)
   npm install -g vercel
   ```

3. **Domain**:
   - dashti.se domain (currently pointing to Azure)
   - Will be updated to point to Vercel

---

## Backend Deployment (Fly.io)

### Step 1: Install and Login

```bash
# Install Fly.io CLI (Windows PowerShell)
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Login
fly auth login
```

### Step 2: Create Fly.io App

```bash
cd backend
fly launch --no-deploy
```

**Configuration prompts**:
- App name: `dashti-portfolio-backend` (or press Enter for auto-generated)
- Region: Choose `arn` (Stockholm, Sweden)
- PostgreSQL: `Yes` (Development config, $0/month)
- Deploy now: `No`

### Step 3: Set Environment Variables

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set secrets
fly secrets set SECRET_KEY="<generated-key>"
fly secrets set ALGORITHM="HS256"
fly secrets set ACCESS_TOKEN_EXPIRE_MINUTES=10080
fly secrets set ENVIRONMENT="production"
fly secrets set DEBUG="False"
```

### Step 4: Create PostgreSQL Database

```bash
# Create database (if not done in Step 2)
fly postgres create --name dashti-portfolio-db --region arn

# Attach to app
fly postgres attach dashti-portfolio-db --app dashti-portfolio-backend
```

### Step 5: Deploy Backend

```bash
fly deploy
```

### Step 6: Run Database Migrations

```bash
# SSH into app
fly ssh console

# Create tables
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
exit
```

### Step 7: Verify

```bash
fly status
fly logs
fly open  # Opens https://dashti-portfolio-backend.fly.dev
```

Visit `/docs` for API documentation.

---

## Frontend Deployment (Vercel)

### Step 1: Deploy via Dashboard (Recommended)

1. Go to [Vercel Dashboard](https://vercel.com/new)
2. Click "Add New Project"
3. Import from GitHub: Select `portfolio-migration`
4. Configure:
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Add Environment Variable:
   - Name: `VITE_API_URL`
   - Value: `https://dashti-portfolio-backend.fly.dev`
6. Click "Deploy"

### Step 2: Configure Custom Domain

1. Go to Project Settings > Domains
2. Add domain: `dashti.se`
3. Vercel provides DNS records

**Update DNS at your registrar**:
```
Type: CNAME
Name: @
Value: cname.vercel-dns.com

Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

DNS propagation: 5-60 minutes

### Alternative: Deploy via CLI

```bash
cd frontend
vercel login
vercel  # First deploy
vercel --prod  # Production deploy
```

---

## CI/CD Setup (GitHub Actions)

### Step 1: Configure GitHub Secrets

Go to GitHub repository > Settings > Secrets > Actions

**Add these secrets**:

1. **FLY_API_TOKEN**:
   ```bash
   fly auth token
   ```

2. **VERCEL_TOKEN**:
   - Go to [Vercel Account > Tokens](https://vercel.com/account/tokens)
   - Create new token

3. **VERCEL_ORG_ID** and **VERCEL_PROJECT_ID**:
   ```bash
   cd frontend
   vercel link
   cat .vercel/project.json  # Copy orgId and projectId
   ```

### Step 2: Push to Trigger Deployment

```bash
git add .
git commit -m "feat: add production deployment"
git push origin main
```

Monitor at: Repository > Actions tab

---

## Database Management

### Connect to Database

```bash
# Connect to PostgreSQL
fly postgres connect -a dashti-portfolio-db

# Inside psql
\dt                           # List tables
SELECT * FROM users LIMIT 10; # Query
\q                            # Exit
```

### Backup Database

```bash
# Create backup
fly postgres backup create -a dashti-portfolio-db

# List backups
fly postgres backup list -a dashti-portfolio-db

# Restore
fly postgres backup restore -a dashti-portfolio-db <backup-id>
```

---

## Monitoring

### Fly.io

```bash
fly logs              # Real-time logs
fly status           # App status
fly checks list      # Health checks
```

### Vercel

- Dashboard: https://vercel.com/dashboard
- Logs: Click deployment > View Function Logs
- Analytics: Project > Analytics

---

## Scaling

### Fly.io Scaling

```bash
# Vertical: Increase VM resources
fly scale vm shared-cpu-2x --memory 2048

# Horizontal: Multiple instances
fly scale count 2

# Database upgrade
fly postgres update --plan standard-1x -a dashti-portfolio-db
```

### Vercel Scaling

Automatic - no configuration needed

---

## Cost Breakdown

### Current (Low Traffic)

| Service | Plan | Cost |
|---------|------|------|
| Vercel Frontend | Hobby (FREE) | $0/month |
| Fly.io Backend | 1GB RAM | $5/month |
| Fly.io PostgreSQL | Development | $0/month |
| **Total** | | **$5/month** |

### High Traffic

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Pro | $20/month |
| Fly.io | 2GB, 2 instances | $20/month |
| PostgreSQL | Standard | $15/month |
| **Total** | | **$55/month** |

---

## Rollback

### Backend

```bash
fly releases           # List releases
fly releases rollback <version>
```

### Frontend

Via Vercel Dashboard:
1. Go to Deployments
2. Find previous version
3. Click > Promote to Production

---

## Troubleshooting

### Backend Issues

**App won't start**:
```bash
fly logs  # Check logs
fly secrets list  # Verify secrets
```

**Database errors**:
```bash
fly postgres connect -a dashti-portfolio-db
```

### Frontend Issues

**Build fails**:
- Check Vercel build logs
- Verify VITE_API_URL is set
- Check Node version (use 20)

**API requests fail**:
- Check CORS in backend
- Verify API URL is correct
- Check browser console

**Domain not working**:
- Verify DNS records
- Wait for propagation (5-60 min)
- Check SSL in Vercel dashboard

---

## Security Checklist

- [+] HTTPS enforced (auto SSL)
- [+] Secrets stored securely
- [+] CORS configured
- [+] Security headers set
- [+] Rate limiting enabled
- [+] Input validation (Pydantic)
- [+] SQL injection prevention (SQLAlchemy)
- [+] XSS protection (Vue 3)

---

## Maintenance Schedule

**Weekly**:
- Monitor logs
- Check resource usage
- Review performance

**Monthly**:
- Update dependencies
- Review backups
- Check access logs

**Quarterly**:
- Security audit
- Optimize queries
- Disaster recovery test

---

## Support

- Fly.io Docs: https://fly.io/docs/
- Vercel Docs: https://vercel.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com/
- Vue 3 Docs: https://vuejs.org/

---

## Architecture Comparison

### Old (Azure)

- Frontend: Azure Static Web Apps
- Backend: None (static site)
- Cost: ~$0-9/month
- Deployment: GitHub Actions

### New (Vercel + Fly.io)

- Frontend: Vercel (Vue 3)
- Backend: Fly.io (FastAPI + PostgreSQL)
- Cost: $0-5/month
- Deployment: GitHub Actions
- Features: Admin panel, API, auth, database

**Benefits**: 8.6x faster, modern stack, full backend

---

Last Updated: 2025-10-28
