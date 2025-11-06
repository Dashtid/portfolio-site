# Quick Start - Fix Portfolio Deployment

**Current Status**: Backend and frontend deployed but not functional
**Time Required**: 15-20 minutes
**Prerequisites**: Terminal access, flyctl installed, Vercel account access

## Problem Summary

1. **Frontend**: Wrong site deployed (Next.js template instead of Vue 3 portfolio)
2. **Backend**: Using SQLite instead of PostgreSQL
3. **Database**: Empty, no content

## Quick Fix Guide

### Step 1: Fix Database Connection (5 min)

**Run this command** - it will prompt for confirmation, type `y`:

```bash
flyctl postgres attach dashti-portfolio-db -a dashti-portfolio-backend
```

**Expected Output**:
```
Postgres cluster dashti-portfolio-db is now attached to dashti-portfolio-backend
The following secret was added to dashti-portfolio-backend:
  DATABASE_URL=postgres://...
```

**Verify it worked**:
```bash
# Wait 30 seconds for restart, then:
flyctl ssh console -a dashti-portfolio-backend -C 'python -c "from app.config import settings; print(settings.async_database_url)"'
```

**Expected**: Should show `postgresql+asyncpg://...` (NOT `sqlite+aiosqlite://`)

---

### Step 2: Populate Database (2 min)

```bash
flyctl ssh console -a dashti-portfolio-backend
```

Once inside the container:
```bash
cd /app
python migrate_real_content.py
python populate_documents.py
python populate_experience_details.py
exit
```

**Expected Output**: Should see messages like:
```
[+] Cleared existing data
[+] Added company: Hermes Medical Solutions
[+] Added company: Scania Engines
...
[OK] Added 7 companies
[OK] Added 4 education entries
```

**Verify it worked**:
```bash
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies | python -m json.tool | head -30
```

Should show JSON array with company data (NOT empty `[]`)

---

### Step 3: Fix Vercel Frontend (5 min)

#### Option A: Vercel Dashboard (Recommended)

1. Go to https://vercel.com/dashboard
2. Click on project: **portfolio-site-psi-three**
3. Click **Settings**
4. Scroll to **Root Directory**
5. Click **Edit**
6. Enter: `frontend`
7. Click **Save**
8. Go to **Deployments** tab
9. Click latest deployment's **...** menu
10. Click **Redeploy**
11. Uncheck "Use existing Build Cache"
12. Click **Redeploy**

Wait 2-3 minutes for build to complete.

#### Option B: Command Line (Alternative)

```bash
# Install Vercel CLI if needed
npm install -g vercel

# Login
vercel login

# Redeploy with correct settings
cd frontend
vercel --prod
```

**Verify it worked**:
```bash
curl -s https://portfolio-site-psi-three.vercel.app/ | grep -i "David Dashti"
```

Should return HTML content (NOT "Inzhagi" or Next.js template)

---

### Step 4: Verify Everything Works (3 min)

#### Test Backend API:
```bash
# Should return 7 companies
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies | python -m json.tool | grep "name"

# Should return 4 education entries
curl https://dashti-portfolio-backend.fly.dev/api/v1/education | python -m json.tool | grep "institution"

# Should return 8 projects
curl https://dashti-portfolio-backend.fly.dev/api/v1/projects | python -m json.tool | grep "name"
```

#### Test Frontend:
Open in browser: https://portfolio-site-psi-three.vercel.app

**Expected to see**:
- Your name: David Dashti
- Professional experience timeline
- Education section
- Projects showcase
- Publications with downloadable PDFs

**Should NOT see**:
- "Welcome, I'm Inzhagi"
- Next.js template
- Blank page
- Error messages

---

## Troubleshooting

### Database attachment fails

**Error**: "consumer app already contains a secret named DATABASE_URL"

**Fix**:
```bash
flyctl secrets unset DATABASE_URL -a dashti-portfolio-backend
# Wait 30 seconds, then retry Step 1
```

### Backend still using SQLite

**Symptom**: `flyctl ssh console` shows `sqlite+aiosqlite://`

**Fix**: Force restart
```bash
flyctl apps restart dashti-portfolio-backend
# Wait 30 seconds
flyctl ssh console -a dashti-portfolio-backend -C 'python -c "from app.config import settings; print(settings.async_database_url)"'
```

### Vercel still shows wrong site

**Symptom**: Still seeing "Inzhagi" or Next.js template

**Fix**: Check Root Directory setting
```bash
# Verify in dashboard: Settings > General > Root Directory
# Should show: "frontend"
# If not set correctly, update and redeploy
```

**Alternative**: Clear deployment cache
```bash
# In Vercel dashboard
# Deployments > Latest > ... > Redeploy
# Uncheck "Use existing Build Cache"
```

### Database population script fails

**Error**: Connection timeout or database errors

**Fix 1**: Verify PostgreSQL is running
```bash
flyctl status -a dashti-portfolio-db
# All machines should show "started"
```

**Fix 2**: Check logs
```bash
flyctl logs -a dashti-portfolio-backend --limit 50
# Look for database connection errors
```

**Fix 3**: Recreate tables manually
```bash
flyctl ssh console -a dashti-portfolio-backend
python -c "
import asyncio
from app.database import engine, Base
async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(create())
"
# Then retry population scripts
```

---

## Success Checklist

Mark complete when:
- [ ] Database shows PostgreSQL (NOT SQLite)
- [ ] Backend API returns company data
- [ ] Frontend shows Vue 3 portfolio (NOT "Inzhagi")
- [ ] Can navigate between pages (Home, Experience, Projects)
- [ ] Experience detail pages work (Hermes, Scania, etc.)
- [ ] PDFs downloadable (Master thesis, Bachelor thesis)
- [ ] No console errors in browser

---

## Next Steps (Optional)

After basic deployment works:

1. **Custom Domain** (15 min)
   - Configure dashti.se in Vercel
   - Update DNS records
   - See docs/DEPLOYMENT.md

2. **Performance Optimization** (30 min)
   - Review Core Web Vitals
   - Optimize images
   - Configure CDN caching

3. **Monitoring** (15 min)
   - Set up uptime monitoring
   - Configure error tracking
   - Enable analytics

---

## Help & Documentation

- **Detailed Guides**:
  - [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) - Complete PostgreSQL guide
  - [docs/VERCEL_FIX.md](docs/VERCEL_FIX.md) - Vercel configuration
  - [docs/DEPLOYMENT_STATUS.md](docs/DEPLOYMENT_STATUS.md) - Current status

- **Backend URL**: https://dashti-portfolio-backend.fly.dev/
- **Frontend URL**: https://portfolio-site-psi-three.vercel.app
- **Fly.io Dashboard**: https://fly.io/dashboard/personal
- **Vercel Dashboard**: https://vercel.com/dashboard

---

## Contact

If you encounter issues not covered here, check the detailed troubleshooting in:
- docs/DATABASE_SETUP.md (database issues)
- docs/VERCEL_FIX.md (frontend issues)
- docs/DEPLOYMENT.md (general deployment)

**Last Updated**: 2025-11-06
