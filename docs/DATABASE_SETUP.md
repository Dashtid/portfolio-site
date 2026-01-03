# Database Setup Guide - Fly.io PostgreSQL

## Current Status

**Issue**: Backend is using SQLite instead of PostgreSQL
**Cause**: DATABASE_URL secret wasn't properly configured
**Solution**: Manually set DATABASE_URL with correct PostgreSQL connection string

## Step-by-Step Fix

### Step 1: Get PostgreSQL Connection String

Run this command to get the internal connection string:

```bash
flyctl postgres attach dashti-portfolio-db -a dashti-portfolio-backend
```

When prompted, confirm "yes". This will:
1. Create DATABASE_URL secret automatically
2. Show the connection string in output
3. Configure internal networking

Expected output:
```
Postgres cluster dashti-portfolio-db is now attached to dashti-portfolio-backend
The following secret was added to dashti-portfolio-backend:
  DATABASE_URL=postgres://...
```

### Step 2: Verify Connection

Wait 30 seconds for app to restart, then check:

```bash
flyctl ssh console -a dashti-portfolio-backend -C 'python -c "from app.config import settings; print(settings.async_database_url)"'
```

Expected output: `postgresql+asyncpg://dashti_portfolio_backend:...@dashti-portfolio-db.internal:5432/dashti_portfolio_backend`

NOT: `sqlite+aiosqlite:///./portfolio.db`

### Step 3: Verify API is Using PostgreSQL

```bash
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies
```

Expected: `[]` (empty array, no data yet)
NOT: Error or timeout

### Step 4: Initialize Database Tables

Tables are created automatically on first API startup. Verify:

```bash
flyctl postgres connect -a dashti-portfolio-db --database dashti_portfolio_backend
```

Then in PostgreSQL:
```sql
\dt
```

Expected tables:
- companies
- education
- projects
- documents
- github_stats

Type `\q` to exit.

### Step 5: Populate Data

From your local machine:

```bash
# SSH into the backend machine
flyctl ssh console -a dashti-portfolio-backend

# Run the migration script
cd /app
python migrate_real_content.py
python populate_documents.py
python populate_experience_details.py

# Exit
exit
```

### Step 6: Verify Data

```bash
curl https://dashti-portfolio-backend.fly.dev/api/v1/companies | python -m json.tool | head -30
```

Expected: JSON array with 7 company objects (Hermes, Scania, FDF, SÖS, Skanska, ABB, KTH)

## Troubleshooting

### Issue: Still shows SQLite after attach

**Solution**: Force restart the app

```bash
flyctl apps restart dashti-portfolio-backend
```

Wait 30 seconds, then verify again.

### Issue: "Error: consumer app already contains a secret named DATABASE_URL"

**Solution**: Unset and re-attach

```bash
flyctl secrets unset DATABASE_URL -a dashti-portfolio-backend
flyctl postgres attach dashti-portfolio-db -a dashti-portfolio-backend
```

### Issue: Connection timeout to PostgreSQL

**Check 1**: Verify PostgreSQL is running

```bash
flyctl status -a dashti-portfolio-db
```

All machines should show "started" status.

**Check 2**: Check PostgreSQL logs

```bash
flyctl logs -a dashti-portfolio-db --limit 100
```

Look for connection errors or crashes.

**Check 3**: Restart PostgreSQL

```bash
flyctl apps restart dashti-portfolio-db
```

Wait 60 seconds for cluster to restart.

### Issue: Tables not created

**Solution**: Trigger table creation manually

```bash
flyctl ssh console -a dashti-portfolio-backend
python -c "
import asyncio
from app.database import engine, Base
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('[OK] Tables created')
asyncio.run(create_tables())
"
```

### Issue: Data population script fails

**Check**: Database connection

```bash
flyctl ssh console -a dashti-portfolio-backend
python -c "
import asyncio
from app.database import AsyncSessionLocal
async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute('SELECT version();')
        print(result.scalar())
asyncio.run(test())
"
```

Expected: PostgreSQL version string

## Alternative: Use SQLite (Not Recommended)

If PostgreSQL continues to have issues, you can temporarily use SQLite on Fly.io:

1. Create persistent volume:
```bash
flyctl volumes create portfolio_data --region arn --size 1 -a dashti-portfolio-backend
```

2. Update fly.toml:
```toml
[[mounts]]
  source = "portfolio_data"
  destination = "/data"
```

3. Set DATABASE_URL:
```bash
flyctl secrets set DATABASE_URL="sqlite+aiosqlite:////data/portfolio.db" -a dashti-portfolio-backend
```

4. Populate data (same as Step 5 above)

**Note**: SQLite is NOT recommended for production. PostgreSQL provides better concurrency, backups, and scalability.

## Next Steps After Database Setup

Once database is working:

1. Deploy frontend to Vercel (see [DEPLOYMENT.md](DEPLOYMENT.md))
2. Test end-to-end connectivity
3. Configure custom domain (dashti.se)
