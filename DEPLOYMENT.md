# Deployment Guide - Portfolio Migration

This guide covers the complete deployment process for the portfolio application to Azure.

## Prerequisites

- Azure account with active subscription
- GitHub account
- Domain name (dashti.se) configured
- Azure CLI installed locally
- Node.js 18+ and Python 3.11+

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   dashti.se                      │
│              (Azure Static Web Apps)              │
├─────────────────────┬──────────────────────────┤
│     Frontend        │        Backend API         │
│   (Vue 3 + Vite)   │    (FastAPI + Python)      │
├─────────────────────┴──────────────────────────┤
│              Azure Blob Storage                  │
│               (Static Assets)                    │
├──────────────────────────────────────────────────┤
│              Azure SQL Database                  │
│             (Production Database)                │
└──────────────────────────────────────────────────┘
```

## Step 1: Azure Resources Setup

### 1.1 Create Resource Group

```bash
az group create \
  --name rg-portfolio \
  --location westeurope
```

### 1.2 Create Static Web App

```bash
az staticwebapp create \
  --name portfolio-dashti \
  --resource-group rg-portfolio \
  --source https://github.com/Dashtid/portfolio-migration \
  --branch main \
  --app-location "/frontend" \
  --api-location "/backend/api" \
  --output-location "dist" \
  --login-with-github
```

### 1.3 Create Azure SQL Database (Optional)

```bash
# Create SQL Server
az sql server create \
  --name portfolio-sql-server \
  --resource-group rg-portfolio \
  --location westeurope \
  --admin-user portfolioadmin \
  --admin-password <secure-password>

# Create Database
az sql db create \
  --resource-group rg-portfolio \
  --server portfolio-sql-server \
  --name portfoliodb \
  --service-objective S0
```

## Step 2: Environment Configuration

### 2.1 Set Azure Static Web App Settings

```bash
# Backend environment variables
az staticwebapp appsettings set \
  --name portfolio-dashti \
  --resource-group rg-portfolio \
  --setting-names \
    SECRET_KEY=<your-secret-key> \
    GITHUB_CLIENT_ID=Ov23lipr5RtWr4jnxefG \
    GITHUB_CLIENT_SECRET=<your-client-secret> \
    GITHUB_USER_ID=47575784 \
    ADMIN_USERNAME=Dashtid \
    DATABASE_URL=<azure-sql-connection-string> \
    CORS_ORIGINS='["https://dashti.se"]'
```

### 2.2 Configure Custom Domain

1. In Azure Portal, navigate to your Static Web App
2. Go to "Custom domains"
3. Add custom domain: dashti.se
4. Configure DNS with your domain provider:
   - Type: CNAME
   - Name: @
   - Value: <your-static-app>.azurestaticapps.net

## Step 3: GitHub Actions Setup

### 3.1 Add GitHub Secrets

In your GitHub repository settings, add these secrets:

- `AZURE_STATIC_WEB_APPS_API_TOKEN` - From Azure Static Web App
- `VITE_API_URL` - https://dashti.se/api
- `GITHUB_CLIENT_SECRET` - Your GitHub OAuth secret

### 3.2 Deploy via GitHub Actions

Push to main branch to trigger automatic deployment:

```bash
git add .
git commit -m "Deploy to Azure"
git push origin main
```

## Step 4: Database Migration

### 4.1 Initial Database Setup

```bash
# SSH into Azure Web App (if using App Service)
az webapp ssh --name portfolio-api --resource-group rg-portfolio

# Run migrations
cd /app
python -m alembic upgrade head

# Create initial admin user
python scripts/create_admin.py
```

### 4.2 Seed Initial Data

```python
# scripts/seed_data.py
import asyncio
from app.database import engine, Base
from app.models.company import Company
from sqlalchemy.ext.asyncio import AsyncSession

async def seed_data():
    async with AsyncSession(engine) as session:
        # Add your initial data here
        company = Company(
            name="Hermes Medical Solutions",
            title="Security Specialist",
            description="...",
            location="Stockholm, Sweden",
            start_date="2022-09-01"
        )
        session.add(company)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_data())
```

## Step 5: Monitoring & Maintenance

### 5.1 Application Insights

```bash
az monitor app-insights component create \
  --app portfolio-insights \
  --location westeurope \
  --resource-group rg-portfolio \
  --application-type web
```

### 5.2 Configure Logging

Add to backend configuration:

```python
# app/config.py
import logging
from applicationinsights import TelemetryClient

tc = TelemetryClient('<instrumentation-key>')
logging.basicConfig(level=logging.INFO)
```

### 5.3 Set Up Alerts

```bash
# CPU usage alert
az monitor metrics alert create \
  --name high-cpu-alert \
  --resource-group rg-portfolio \
  --scopes <resource-id> \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m
```

## Step 6: Backup Strategy

### 6.1 Database Backup

```bash
# Create backup
az sql db export \
  --resource-group rg-portfolio \
  --server portfolio-sql-server \
  --database portfoliodb \
  --storage-key <storage-key> \
  --storage-key-type StorageAccessKey \
  --storage-uri https://<account>.blob.core.windows.net/backups/backup.bacpac
```

### 6.2 Automated Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="portfolio_backup_$DATE.bacpac"

az sql db export \
  --resource-group rg-portfolio \
  --server portfolio-sql-server \
  --database portfoliodb \
  --storage-key $STORAGE_KEY \
  --storage-key-type StorageAccessKey \
  --storage-uri "https://$STORAGE_ACCOUNT.blob.core.windows.net/backups/$BACKUP_NAME"

echo "Backup completed: $BACKUP_NAME"
```

## Step 7: Performance Optimization

### 7.1 Frontend Optimization

1. **Enable CDN**:
```bash
az cdn profile create \
  --name portfolio-cdn \
  --resource-group rg-portfolio \
  --sku Standard_Microsoft
```

2. **Configure Caching**:
- Static assets: 1 year cache
- API responses: No cache or short cache
- HTML: No cache

### 7.2 Backend Optimization

1. **Database Indexes**: Create indexes for frequently queried fields
2. **Connection Pooling**: Configure in SQLAlchemy
3. **Response Caching**: Use Redis for API response caching

## Step 8: Security Hardening

### 8.1 Security Headers

Configure in `staticwebapp.config.json`:
- Content Security Policy
- X-Frame-Options
- X-Content-Type-Options
- Referrer Policy

### 8.2 Rate Limiting

Implement rate limiting in FastAPI:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/companies")
@limiter.limit("30/minute")
async def get_companies():
    pass
```

### 8.3 SSL/TLS Configuration

- Force HTTPS redirect
- Configure HSTS header
- Use TLS 1.2+ only

## Deployment Checklist

- [ ] Azure resources created
- [ ] Environment variables configured
- [ ] GitHub secrets added
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Database migrated and seeded
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Performance optimization applied
- [ ] Health checks passing
- [ ] Smoke tests completed

## Rollback Procedure

If deployment fails:

1. **Revert GitHub commit**:
```bash
git revert HEAD
git push origin main
```

2. **Restore database backup** (if needed):
```bash
az sql db import \
  --resource-group rg-portfolio \
  --server portfolio-sql-server \
  --database portfoliodb \
  --storage-key <storage-key> \
  --storage-key-type StorageAccessKey \
  --storage-uri https://<account>.blob.core.windows.net/backups/last-known-good.bacpac
```

3. **Check application logs**:
```bash
az staticwebapp logs show \
  --name portfolio-dashti \
  --resource-group rg-portfolio
```

## Support & Troubleshooting

### Common Issues

1. **Build fails**: Check Node/Python versions
2. **API 404**: Verify API location in config
3. **Auth fails**: Check GitHub OAuth settings
4. **Database connection**: Verify connection string

### Useful Commands

```bash
# View deployment status
az staticwebapp show --name portfolio-dashti

# Stream logs
az staticwebapp logs show --name portfolio-dashti --tail

# Reset deployment
az staticwebapp reset --name portfolio-dashti

# Test locally with Azure CLI
swa start ./frontend/dist --api-location ./backend/api
```

## Cost Optimization

- Use Free tier for Static Web Apps (100GB bandwidth/month)
- Schedule database to pause during low traffic
- Use Azure Blob Storage for media files
- Monitor and optimize based on usage patterns

## Contact

For deployment issues or questions:
- Email: david@dashti.se
- GitHub: @Dashtid

---

Last Updated: October 2025
Version: 1.0