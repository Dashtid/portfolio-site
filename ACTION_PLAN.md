# Action Plan - Complete Portfolio Deployment

**Status**: Ready for final configuration
**Time Required**: 15-20 minutes total
**Last Updated**: 2025-11-06

## Situation Overview

### What's Working
- [OK] Backend deployed to Fly.io
- [OK] Frontend deployed to Vercel
- [OK] PostgreSQL database created
- [OK] GitHub repository public
- [OK] .dockerignore fixed (no more .env conflicts)
- [OK] Comprehensive documentation created

### What Needs Fixing (3 Tasks)
1. **PostgreSQL Connection** - Backend needs DATABASE_URL configured
2. **Vercel Root Directory** - Frontend needs correct build path
3. **Database Population** - Content needs to be loaded

---

## Task 1: Connect PostgreSQL (5 minutes)

### Why This is Needed
The backend is currently using SQLite because the DATABASE_URL secret isn't set. PostgreSQL is running but not connected to the backend app.

### What You Need to Do

**Run this command**:
```bash
flyctl postgres attach dashti-portfolio-db -a dashti-portfolio-backend
```

**You'll see this prompt**:
```
Postgres cluster dashti-portfolio-db is now attached to dashti-portfolio-backend
The following secret was added to dashti-portfolio-backend:
  DATABASE_URL=postgres://dashti_portfolio_backend:xxxxx@dashti-portfolio-db.internal:5432/dashti_portfolio_backend

Continue? (y/N)
```

**Type**: `y` and press Enter

### Verification

Wait 30 seconds for the backend to restart, then run:
```bash
flyctl ssh console -a dashti-portfolio-backend -C 'python -c "from app.config import settings; print(settings.async_database_url)"'
```

**Expected Output**:
```
postgresql+asyncpg://dashti_portfolio_backend:xxxxx@dashti-portfolio-db.internal:5432/dashti_portfolio_backend
```

**NOT**: `sqlite+aiosqlite:////data/portfolio.db`

If you still see SQLite, run:
```bash
flyctl apps restart dashti-portfolio-backend
```

Wait 30 seconds and check again.

---

## Task 2: Populate Database (2 minutes)

### Why This is Needed
The database tables exist but are empty. We need to load your portfolio content (companies, education, projects, PDFs).

### What You Need to Do

**Step 1**: SSH into backend
```bash
flyctl ssh console -a dashti-portfolio-backend
```

**Step 2**: Run migration scripts (inside the container)
```bash
cd /app
python migrate_real_content.py
```

**Expected Output**:
```
[+] Cleared existing data
[+] Added company: Hermes Medical Solutions
[+] Added company: Scania Engines
[+] Added company: Finnish Defence Forces
[+] Added company: Södersjukhuset - SÖS
[+] Added company: Skanska Infrastructure Development
[+] Added company: ABB Power Grids - Hitachi Energy
[+] Added company: KTH Royal Institute of Technology
[OK] Added 7 companies
[+] Added education: KTH Royal Institute of Technology
[+] Added education: KTH Royal Institute of Technology
[+] Added education: LTH - Faculty of Engineering
[+] Added education: Ekerö Gymnasium
[OK] Added 4 education entries
```

**Step 3**: Continue with remaining scripts
```bash
python populate_documents.py
python populate_experience_details.py
```

**Step 4**: Exit container
```bash
exit
```

### Verification

```bash
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies | python -m json.tool | grep "name"
```

**Expected**: Should see 7 company names

---

## Task 3: Fix Vercel Frontend (5 minutes)

### Why This is Needed
Vercel is currently deploying from the repository root, finding a Next.js config, and building the wrong site. We need to tell it to build from the `frontend/` directory.

### What You Need to Do

#### Method A: Vercel Dashboard (Recommended)

1. Go to: https://vercel.com/dashboard
2. Find and click project: `portfolio-site-psi-three`
3. Click `Settings` (top navigation)
4. Scroll down to **Root Directory** section
5. Click `Edit` button
6. Enter: `frontend`
7. Click `Save`
8. Go to `Deployments` tab
9. Find latest deployment
10. Click the `...` (three dots) menu
11. Click `Redeploy`
12. **UNCHECK** "Use existing Build Cache"
13. Click `Redeploy`

Wait 2-3 minutes for deployment to complete.

#### Method B: Vercel CLI (Alternative)

```bash
npm install -g vercel  # If not already installed
vercel login
cd frontend
vercel --prod
```

### Verification

```bash
curl -s https://portfolio-site-psi-three.vercel.app/ | grep -i "David Dashti"
```

**Expected**: Should return HTML with your name

**NOT**: "Welcome, I'm Inzhagi" or empty response

**Browser Test**: Open https://portfolio-site-psi-three.vercel.app/
- Should see your portfolio
- Navigation should work (Home, Experience, Projects)
- Experience detail pages should load (Hermes, Scania, etc.)
- No console errors

---

## Final Verification (3 minutes)

### Test All Endpoints

```bash
# Companies
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies | python -m json.tool | grep "name"

# Education
curl https://dashti-portfolio-backend.fly.dev/api/v1/education | python -m json.tool | grep "institution"

# Projects
curl https://dashti-portfolio-backend.fly.dev/api/v1/projects | python -m json.tool | grep "name"

# Documents
curl https://dashti-portfolio-backend.fly.dev/api/v1/documents | python -m json.tool | grep "title"
```

### Test Frontend

1. Open: https://portfolio-site-psi-three.vercel.app/
2. Verify homepage loads with your content
3. Click "Experience" - should show timeline
4. Click a company (e.g., Hermes) - detail page should load
5. Click "Projects" - should show project cards
6. Click "Publications" - PDFs should be downloadable
7. Open browser DevTools Console - should see no errors

---

## Success Criteria

Your portfolio is fully functional when:

- [ ] Backend uses PostgreSQL (not SQLite)
- [ ] Backend API returns data (7 companies, 4 education, 8 projects)
- [ ] Frontend shows Vue 3 portfolio (NOT "Inzhagi" site)
- [ ] Homepage displays correctly
- [ ] Navigation works (Home, Experience, Projects, Publications)
- [ ] Experience detail pages work
- [ ] Projects showcase displays
- [ ] PDFs are downloadable
- [ ] No browser console errors
- [ ] API calls from frontend to backend work

---

## Timeline

| Task | Time | Status |
|------|------|--------|
| Connect PostgreSQL | 5 min | Pending (interactive) |
| Populate Database | 2 min | Pending |
| Fix Vercel Frontend | 5 min | Pending (interactive) |
| Verification | 3 min | Pending |
| **Total** | **15 min** | **Ready to start** |

---

## Troubleshooting

If something doesn't work, see:
- [QUICK_START.md](QUICK_START.md) - Step-by-step with troubleshooting
- [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) - Detailed database guide
- [docs/VERCEL_FIX.md](docs/VERCEL_FIX.md) - Vercel configuration details
- [docs/DEPLOYMENT_STATUS.md](docs/DEPLOYMENT_STATUS.md) - Current status

---

## After Deployment

Once everything works, you can optionally:

1. **Configure Custom Domain** (15 min)
   - Set up dashti.se in Vercel
   - Update DNS records

2. **Archive Old Site** (5 min)
   - Take down Azure deployment
   - Update social media links

3. **Performance Tuning** (30 min)
   - Optimize images
   - Configure CDN caching
   - Review Core Web Vitals

---

## Commands Cheat Sheet

```bash
# Task 1: Connect PostgreSQL
flyctl postgres attach dashti-portfolio-db -a dashti-portfolio-backend

# Verify connection
flyctl ssh console -a dashti-portfolio-backend -C 'python -c "from app.config import settings; print(settings.async_database_url)"'

# Task 2: Populate Database
flyctl ssh console -a dashti-portfolio-backend
cd /app && python migrate_real_content.py && python populate_documents.py && python populate_experience_details.py && exit

# Verify data
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies | python -m json.tool | grep "name"

# Task 3: Fix Vercel
# (Use dashboard - see Method A above)

# Verify frontend
curl -s https://portfolio-site-psi-three.vercel.app/ | grep -i "David Dashti"
```

---

**Ready to start? Begin with Task 1: Connect PostgreSQL**
