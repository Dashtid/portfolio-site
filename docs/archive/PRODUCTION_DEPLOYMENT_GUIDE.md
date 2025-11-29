# Production Deployment Fix Guide

**Last Updated**: 2025-11-05
**Status**: REQUIRES MANUAL ACTION

## Current Status

### [!] Issues Identified

1. **Fly.io Backend (503 Error)**
   - URL: https://dashti-portfolio-backend.fly.dev
   - Status: Service Unavailable (503)
   - Issue: App not running or needs redeployment

2. **Vercel Frontend (Wrong Site)**
   - URL: https://portfolio-site-psi-three.vercel.app
   - Status: Showing "Inzhagi" Next.js app instead of your Vue 3 portfolio
   - Issue: Wrong GitHub repository connected

3. **GitHub Actions (Not Configured)**
   - Workflows created but secrets not configured
   - Requires manual setup of deployment tokens

### [+] What's Working

- **Local Development**: Both frontend and backend running perfectly
  - Frontend: http://localhost:3000 (Vue 3 portfolio with data)
  - Backend: http://localhost:8000 (FastAPI with seeded database)
- **Database**: 3 companies, 5 projects, 19 skills, 5 education items
- **Code**: All tests passing, builds successful
- **Fly.io CLI**: Installed at `C:\Users\david\.fly\bin\flyctl.exe`

---

## Fix #1: Deploy Backend to Fly.io

### Prerequisites

- Fly.io account (already exists)
- Backend app `dashti-portfolio-backend` (already created)

### Steps

#### 1. Authenticate with Fly.io

```powershell
# Open PowerShell
C:\Users\david\.fly\bin\flyctl.exe auth login
```

This opens a browser for authentication. Follow the prompts.

#### 2. Check App Status

```powershell
cd C:\Code\portfolio-site\backend
C:\Users\david\.fly\bin\flyctl.exe status -a dashti-portfolio-backend
```

Expected output: Shows app status (running, stopped, or crashed)

#### 3. Redeploy Backend

```powershell
cd C:\Code\portfolio-site\backend
C:\Users\david\.fly\bin\flyctl.exe deploy --remote-only
```

[!] This will:
- Build Docker image on Fly.io servers
- Deploy to production
- Run health checks
- Take ~3-5 minutes

#### 4. Verify Deployment

```powershell
# Test health endpoint
curl https://dashti-portfolio-backend.fly.dev/api/v1/health
```

Expected: `{"status":"healthy","timestamp":"...","service":"portfolio-api"}`

#### 5. Seed Production Database

```powershell
# SSH into Fly.io app
C:\Users\david\.fly\bin\flyctl.exe ssh console -a dashti-portfolio-backend

# Once connected, run seed script
python -m app.seed_data

# Exit SSH
exit
```

#### 6. Verify Data

```powershell
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies/
```

Expected: JSON array with 3 companies

---

## Fix #2: Deploy Frontend to Vercel

### Option A: Via Vercel Dashboard (Recommended)

#### 1. Login to Vercel

Visit: https://vercel.com/dashboard

#### 2. Find Project

- Look for project: `portfolio-site-psi-three`
- Click on it to open

#### 3. Check Git Connection

- Go to **Settings** → **Git**
- Under "Connected Git Repository", check which repo is connected
- **Expected**: `Dashtid/portfolio-migration` on branch `main`
- **If wrong**: Click "Disconnect" then reconnect correct repo

#### 4. Trigger Redeploy

- Go to **Deployments** tab
- Find latest deployment
- Click **...** (three dots) → **Redeploy**
- Check "Use existing Build Cache"
- Click "Redeploy"

#### 5. Verify Deployment

Visit: https://portfolio-site-psi-three.vercel.app

**Expected**: Your Vue 3 portfolio with "David Dashti | Cybersecurity in Healthcare"
**NOT**: "Welcome, I'm Inzhagi" Next.js site

### Option B: Via Vercel CLI

#### 1. Install Vercel CLI

```powershell
npm install -g vercel
```

#### 2. Login

```powershell
vercel login
```

Follow email verification prompts

#### 3. Link Project

```powershell
cd C:\Code\portfolio-site\frontend
vercel link
```

Select your project when prompted

#### 4. Deploy

```powershell
vercel --prod
```

#### 5. Verify

The CLI will output the production URL. Visit it to verify.

---

## Fix #3: Configure GitHub Actions Secrets

### Prerequisites

- GitHub repository: `Dashtid/portfolio-migration`
- Fly.io and Vercel accounts

### Required Secrets

#### 1. Fly.io Deployment Token

**Get Token**:
```powershell
C:\Users\david\.fly\bin\flyctl.exe auth token
```

**Add to GitHub**:
1. Go to https://github.com/Dashtid/portfolio-migration/settings/secrets/actions
2. Click "New repository secret"
3. Name: `FLY_API_TOKEN`
4. Value: [paste token from command above]
5. Click "Add secret"

#### 2. Vercel Deployment Tokens

**Get Tokens**:
1. Visit https://vercel.com/account/tokens
2. Click "Create Token"
3. Name it "GitHub Actions"
4. Copy the token (save it, shown only once)

**Get Org ID and Project ID**:
1. Go to your project settings: https://vercel.com/[username]/portfolio-site-psi-three/settings
2. **Org ID**: Find in General settings
3. **Project ID**: Find in General settings

**Add to GitHub**:
1. Go to https://github.com/Dashtid/portfolio-migration/settings/secrets/actions
2. Add three secrets:
   - `VERCEL_TOKEN`: [token from step above]
   - `VERCEL_ORG_ID`: [from project settings]
   - `VERCEL_PROJECT_ID`: [from project settings]

### Test GitHub Actions

#### 1. Trigger Manual Workflow

1. Go to https://github.com/Dashtid/portfolio-migration/actions
2. Select "Deploy Backend to Fly.io" or "Deploy Frontend to Vercel"
3. Click "Run workflow"
4. Select `main` branch
5. Click "Run workflow"

#### 2. Verify Deployment

Check the Actions tab for green checkmarks ✓

---

## Post-Deployment Verification Checklist

### Backend

- [ ] Health endpoint returns 200: https://dashti-portfolio-backend.fly.dev/api/v1/health
- [ ] Companies API returns data: https://dashti-portfolio-backend.fly.dev/api/v1/companies/
- [ ] Projects API returns data: https://dashti-portfolio-backend.fly.dev/api/v1/projects/
- [ ] Skills API returns data: https://dashti-portfolio-backend.fly.dev/api/v1/skills/
- [ ] Education API returns data: https://dashti-portfolio-backend.fly.dev/api/v1/education/
- [ ] API docs accessible: https://dashti-portfolio-backend.fly.dev/api/docs

### Frontend

- [ ] Site loads: https://portfolio-site-psi-three.vercel.app
- [ ] Shows correct Vue 3 portfolio (NOT "Inzhagi" Next.js)
- [ ] Title: "David Dashti | Cybersecurity in Healthcare"
- [ ] Experience section displays companies
- [ ] Projects section displays projects
- [ ] Skills section displays skills
- [ ] Education section displays education
- [ ] Frontend→Backend API calls work

### GitHub Actions

- [ ] CI workflow runs on PR creation
- [ ] Backend deploy workflow runs on push to main (backend changes)
- [ ] Frontend deploy workflow runs on push to main (frontend changes)
- [ ] All tests passing
- [ ] Deployments succeed

---

## Troubleshooting

### Fly.io Backend Issues

**Problem**: Deployment fails with "error connecting to database"

**Solution**:
```powershell
# Check database status
C:\Users\david\.fly\bin\flyctl.exe postgres list

# If database not running
C:\Users\david\.fly\bin\flyctl.exe postgres start [database-name]
```

**Problem**: App crashes after deployment

**Solution**:
```powershell
# Check logs
C:\Users\david\.fly\bin\flyctl.exe logs -a dashti-portfolio-backend

# Look for Python errors or missing environment variables
```

**Problem**: "SECRET_KEY not set"

**Solution**:
```powershell
# Set secret
C:\Users\david\.fly\bin\flyctl.exe secrets set SECRET_KEY=[generate-random-key] -a dashti-portfolio-backend

# Generate random key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Vercel Frontend Issues

**Problem**: Build fails with "command not found: vite"

**Solution**:
- Check `frontend/package.json` has correct build command
- Ensure `node_modules` is in `.gitignore`
- Vercel will run `npm install` automatically

**Problem**: API calls fail (CORS errors)

**Solution**:
- Update backend CORS origins to include Vercel URL
- Add to `backend/.env` or Fly.io secrets:
  ```
  CORS_ORIGINS='["https://portfolio-site-psi-three.vercel.app"]'
  ```

### GitHub Actions Issues

**Problem**: "FLY_API_TOKEN" not found

**Solution**:
- Verify secret name matches exactly (case-sensitive)
- Regenerate token if expired
- Check secret is in repository (not organization) secrets

---

## Next Steps After Deployment

### 1. Configure Custom Domain (Optional)

**Point dashti.se to Vercel**:
1. Go to Vercel project settings → Domains
2. Add custom domain: `dashti.se`
3. Follow DNS configuration instructions
4. Update CORS in backend to include `https://dashti.se`

### 2. Enable Monitoring

**Fly.io Metrics**:
```powershell
C:\Users\david\.fly\bin\flyctl.exe dashboard -a dashti-portfolio-backend
```

**Vercel Analytics**:
- Enable in Vercel project settings → Analytics

### 3. Set Up Backups

**Database Backups** (Fly.io PostgreSQL):
```powershell
C:\Users\david\.fly\bin\flyctl.exe postgres backup list -a [db-name]
```

---

## Summary

**What You Need To Do**:

1. **Fly.io Backend** (~10 minutes):
   - Run: `flyctl auth login`
   - Run: `flyctl deploy --remote-only` in backend directory
   - Run: `flyctl ssh console` then `python -m app.seed_data`

2. **Vercel Frontend** (~5 minutes):
   - Option A: Dashboard → Disconnect wrong repo → Connect correct repo → Redeploy
   - Option B: CLI → `vercel link` → `vercel --prod`

3. **GitHub Actions** (~5 minutes):
   - Get Fly.io token: `flyctl auth token`
   - Get Vercel tokens from dashboard
   - Add all 4 secrets to GitHub

**Total Time**: ~20 minutes

**Result**: Fully automated CI/CD pipeline with production deployments working!

---

## Support

**Issues?**
- Fly.io: https://community.fly.io
- Vercel: https://vercel.com/support
- GitHub Actions: https://github.com/Dashtid/portfolio-migration/actions

**Local Development Working?**
If local works but production doesn't, compare environment variables and secrets.
