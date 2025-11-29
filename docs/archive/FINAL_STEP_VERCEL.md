# Final Step: Fix Vercel Frontend Deployment

## Current Status

Completed:
- Backend deployed and running on Fly.io
- PostgreSQL database connected successfully
- Database populated with 7 companies and 4 education entries
- API verified working: https://dashti-portfolio-backend.fly.dev/api/v1/companies/

Remaining:
- Frontend showing wrong site (Next.js template instead of Vue 3 portfolio)
- Vercel needs Root Directory configured to `frontend/`

## The Problem

Vercel is currently deploying from the repository root, finding a Next.js config somewhere, and building the wrong site. You're seeing "Inzhagi" or a Next.js template instead of your Vue 3 portfolio.

---

## The Solution (2 minutes)

You need to set the Root Directory in Vercel dashboard. **This cannot be automated** - you must do this manually.

### Step 1: Go to Vercel Dashboard

1. Open https://vercel.com/dashboard
2. Find your project: `portfolio-site-psi-three` (or similar name)
3. Click on the project

### Step 2: Configure Root Directory

1. Click Settings (top navigation bar)
2. Scroll down to Root Directory section
3. Click Edit button
4. Enter: `frontend`
5. Click Save

### Step 3: Redeploy

1. Go to Deployments tab (top navigation)
2. Find the latest deployment
3. Click the ... (three dots) menu next to it
4. Click Redeploy
5. IMPORTANT: UNCHECK "Use existing Build Cache"
6. Click Redeploy

Wait 2-3 minutes for the deployment to complete.

## Verification

Once redeployment finishes:

### Check the site loads:
```bash
curl -s https://portfolio-site-psi-three.vercel.app/ | grep -i "David Dashti"
```

Expected: Should return HTML with your name
Not expected: "Welcome, I'm Inzhagi" or empty response

### Open in browser:
https://portfolio-site-psi-three.vercel.app/

**You should see:**
- Your Vue 3 portfolio homepage
- Navigation (Home, Experience, Projects, Publications)
- Experience timeline with your companies
- No console errors

---

## API Integration Test

After frontend is fixed, verify it connects to backend:

1. Open https://portfolio-site-psi-three.vercel.app/
2. Click **Experience** in navigation
3. You should see:
   - Hermes Medical Solutions
   - Scania Engines
   - Finnish Defence Forces
   - Södersjukhuset - SÖS
   - SoftPro Medical Solutions
   - Karolinska University Hospital
   - Philips Healthcare

4. Click on any company (e.g., Hermes)
5. Detail page should load with company information

## Troubleshooting

### If site still shows wrong content

Problem: Build cache wasn't cleared
Fix: Redeploy again with "Use existing Build Cache" UNCHECKED

### If you get 404 errors

Problem: Root Directory path is wrong
Fix:
1. Go back to Settings → Root Directory
2. Make sure it's exactly: `frontend` (no leading/trailing slashes)
3. Save and redeploy

### If API calls fail (CORS errors)

Problem: Backend CORS not configured
Check: Look in browser DevTools Console for CORS errors
Note: Backend already has CORS configured for Vercel domains, this should work

## After Success

Once the frontend loads correctly and shows your portfolio:

### Optional Next Steps:

1. **Configure Custom Domain** (if you want dashti.se):
   - Add custom domain in Vercel dashboard
   - Update DNS records

2. **Monitor Backend:**
   ```bash
   flyctl status -a dashti-portfolio-backend
   flyctl logs -a dashti-portfolio-backend
   ```

3. **Check Database:**
   ```bash
   flyctl postgres connect -a dashti-portfolio-db -d dashti_portfolio_backend
   # Then: SELECT COUNT(*) FROM companies;
   ```

## Complete Deployment Summary

Once Vercel is fixed, you'll have:

Backend (Fly.io):
- App: dashti-portfolio-backend
- Database: PostgreSQL (dashti-portfolio-db)
- API: https://dashti-portfolio-backend.fly.dev/api/v1/
- Status: Running, Connected, Populated

Frontend (Vercel):
- App: portfolio-site-psi-three
- URL: https://portfolio-site-psi-three.vercel.app/
- Status: Needs Root Directory fix

Database Content:
- 7 Companies (populated)
- 4 Education Entries (populated)
- 0 Projects (can be added later)
- 0 Documents (can be added later)

## Quick Commands Reference

```bash
# Verify backend health
curl https://dashti-portfolio-backend.fly.dev/api/v1/health

# Check companies API
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies/ | python -m json.tool

# Check education API
curl https://dashti-portfolio-backend.fly.dev/api/v1/education/ | python -m json.tool

# Test frontend (after fix)
curl -s https://portfolio-site-psi-three.vercel.app/ | grep "David Dashti"
```

Ready to fix? Go to https://vercel.com/dashboard and follow Step 1-3 above.
