# Vercel Configuration Fix

**Issue**: Wrong site deployed (Next.js template instead of Vue 3 portfolio)

**Root Cause**: Vercel project is either:
1. Connected to wrong GitHub repository, OR
2. Deploying from root directory instead of `frontend/` directory

## Fix Steps (Vercel Dashboard)

### Step 1: Verify GitHub Repository Connection

1. Go to https://vercel.com/dashboard
2. Find project: `portfolio-site-psi-three`
3. Click Settings
4. Go to Git section
5. Verify Connected Git Repository: `Dashtid/portfolio-site`
6. If wrong repository:
   - Disconnect current repository
   - Connect to `Dashtid/portfolio-site`
   - Select branch: `main`

### Step 2: Configure Root Directory

1. In Settings, go to "General" section
2. Find "Root Directory" setting
3. Click "Edit"
4. Set Root Directory to: `frontend`
5. Click "Save"

### Step 3: Verify Build Settings

1. In Settings, go to "Build & Development Settings"
2. Verify:
   - Framework Preset: `Vite`
   - Build Command: `npm run build` (or leave blank for auto-detect)
   - Output Directory: `dist` (or leave blank for auto-detect)
   - Install Command: `npm install` (or leave blank for auto-detect)

### Step 4: Configure Environment Variables

1. In Settings, go to "Environment Variables"
2. Add these variables (Production):
   - `VITE_API_URL`: `https://dashti-portfolio-backend.fly.dev`
   - `VITE_ENVIRONMENT`: `production`

### Step 5: Trigger Redeploy

1. Go to Deployments tab
2. Click "..." menu on latest deployment
3. Click "Redeploy"
4. Select "Use existing Build Cache" = NO
5. Click "Redeploy"

### Step 6: Verify Deployment

Wait 2-3 minutes for build to complete, then check:

```bash
curl -s https://portfolio-site-psi-three.vercel.app/ | grep -i "David Dashti\|Portfolio"
```

Expected: Should see Vue 3 portfolio, NOT "Welcome, I'm Inzhagi"

## Alternative: Create New Vercel Project

If above steps don't work, create fresh project:

1. Go to https://vercel.com/new
2. Import `Dashtid/portfolio-site` from GitHub
3. Configure project:
   - Project Name: `portfolio-site` (or keep auto-generated)
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Settings: Leave as defaults
4. Add Environment Variables:
   - `VITE_API_URL`: `https://dashti-portfolio-backend.fly.dev`
   - `VITE_ENVIRONMENT`: `production`
5. Click "Deploy"
6. Update custom domain `dashti.se` to point to new project

## Troubleshooting

**Build fails with "command not found"**:
- Ensure Root Directory is set to `frontend`
- Ensure `package.json` exists in `frontend/` directory

**Deployment succeeds but shows blank page**:
- Check browser console for API errors
- Verify VITE_API_URL environment variable is set
- Check CORS settings on backend

**Still shows wrong site**:
- Double-check Git repository connection
- Delete old project and create new one
- Clear Vercel cache in Build settings
