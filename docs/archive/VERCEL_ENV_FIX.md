# Vercel Environment Variable Fix

## Issue
The frontend deployment on Vercel was showing a broken layout because it was trying to connect to `https://api.dashti.se` (which doesn't exist) instead of the actual backend at `https://dashti-portfolio-backend.fly.dev`.

## Root Cause
The `VITE_API_URL` environment variable in Vercel was not set correctly.

## Solution

### Option 1: Set via Vercel Web Interface (Recommended)

1. Go to your Vercel project: https://vercel.com/dashboard
2. Select the `portfolio-site` project
3. Go to **Settings** > **Environment Variables**
4. Add or update the following variable:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://dashti-portfolio-backend.fly.dev`
   - **Environments**: Production, Preview, Development (check all)
5. Click **Save**
6. Go to **Deployments** and click **Redeploy** on the latest deployment

### Option 2: Set via Vercel CLI

```bash
# Install Vercel CLI if not already installed
npm install -g vercel

# Login to Vercel
vercel login

# Set environment variable (from project root)
vercel env add VITE_API_URL production
# When prompted, enter: https://dashti-portfolio-backend.fly.dev

# Repeat for preview and development
vercel env add VITE_API_URL preview
vercel env add VITE_API_URL development

# Trigger a new deployment
cd frontend
vercel --prod
```

### Option 3: Quick Redeploy (if env var already set)

If the environment variable is already set in Vercel, you can trigger a new deployment by pushing an empty commit:

```bash
git commit --allow-empty -m "fix: trigger Vercel redeploy with correct VITE_API_URL"
git push origin main
```

## Verification

After redeployment, verify the fix:

1. Open the deployed site: https://portfolio-site-jade-five.vercel.app/
2. Open browser DevTools (F12) > Network tab
3. Reload the page
4. Check that API requests are going to `https://dashti-portfolio-backend.fly.dev/api/v1/companies/` (not `api.dashti.se`)
5. Verify that experience cards are loading with company data

## Local Testing

The local `.env.production` file has been updated with the correct URL:

```bash
cd frontend
npm run build
npm run preview
```

Visit http://localhost:4173 and verify the production build works locally.

## Files Modified

- `frontend/.env.production` - Updated `VITE_API_URL` to `https://dashti-portfolio-backend.fly.dev` (not committed due to .gitignore)
- `VERCEL_ENV_FIX.md` - This documentation file
