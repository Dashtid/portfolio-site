# PostgreSQL Connection Fix - CRITICAL ISSUE FOUND

## Problem Discovered

When you ran `flyctl postgres attach dashti-portfolio-db -a dashti-portfolio-backend --database-user portfolio_app`, it set a DATABASE_URL with this format:

```
postgres://portfolio_app:PASSWORD@dashti-portfolio-db.internal:5432/dashti_portfolio_backend?sslmode=disable
```

**The issue**: The `?sslmode=disable` parameter is **incompatible with asyncpg** (the async PostgreSQL driver we use).

Error from logs:
```
TypeError: connect() got an unexpected keyword argument 'sslmode'
ERROR: Application startup failed. Exiting.
```

## Root Cause

1. Fly.io's `postgres attach` command adds `?sslmode=disable` to DATABASE_URL
2. Our backend/app/config.py converts `postgres://` to `postgresql+asyncpg://`
3. `asyncpg` driver doesn't support the `sslmode` query parameter (it uses a different SSL configuration method)
4. Backend crashes on startup when trying to connect

## Solution Options

### Option 1: Manual Password Reset (REQUIRES YOUR ACTION)

You need to run this command interactively to reset the `portfolio_app` password:

```bash
flyctl postgres connect -a dashti-portfolio-db
```

This will open a PostgreSQL console. Then paste this command:

```sql
ALTER USER portfolio_app WITH PASSWORD 'NEW_SECURE_PASSWORD_HERE';
\q
```

Replace `NEW_SECURE_PASSWORD_HERE` with a secure password (I generated one: `009cdc73b9988e90bd524747c54b0920c490f0f216a94b6ca878375d68bccac0`).

Then set the DATABASE_URL without `sslmode`:

```bash
flyctl secrets set DATABASE_URL="postgres://portfolio_app:NEW_SECURE_PASSWORD_HERE@dashti-portfolio-db.internal:5432/dashti_portfolio_backend" -a dashti-portfolio-backend
```

### Option 2: Use the Postgres Superuser

**Easier approach** - we can use the `postgres` superuser instead:

1. Get the postgres superuser password:
```bash
flyctl postgres connect -a dashti-portfolio-db
```

This command will show you the connection string with the postgres password.

2. Set DATABASE_URL using the postgres user:
```bash
flyctl secrets set DATABASE_URL="postgres://postgres:POSTGRES_PASSWORD@dashti-portfolio-db.internal:5432/dashti_portfolio_backend" -a dashti-portfolio-backend
```

### Option 3: Re-attach Without sslmode (RECOMMENDED - FASTEST)

The `flyctl postgres attach` command was designed to work with traditional sync PostgreSQL drivers that support `sslmode`. For async drivers, we need to manually configure.

1. First, let me check what password was set when you ran attach. Run this:
```bash
flyctl ssh console -a dashti-portfolio-db
```

2. Inside the container, run:
```bash
cat /etc/environment | grep DATABASE
```

Or we can query directly for the user:
```bash
psql postgres://postgres@top2.nearest.of.dashti-portfolio-db.internal:5432 -c "\du portfolio_app"
```

## Current Status

- [X] DATABASE_URL secret exists
- [X] `portfolio_app` user exists in PostgreSQL
- [X] Backend deployment successful
- [ ] **BLOCKED**: Password authentication fails (wrong password in DATABASE_URL)
- [ ] PostgreSQL connection not working

## Next Steps

Please choose Option 1 or Option 2 above and run the commands. Once DATABASE_URL is set correctly (WITHOUT `?sslmode=disable`), the backend will:

1. Automatically restart
2. Connect to PostgreSQL
3. Create tables
4. Be ready for data population

After you run the fix, I can verify with:
```bash
flyctl ssh console -a dashti-portfolio-backend -C 'python -c "from app.config import settings; print(settings.async_database_url)"'
```

Expected output: `postgresql+asyncpg://portfolio_app:...@dashti-portfolio-db.internal:5432/dashti_portfolio_backend`

## Why This Happened

The `flyctl postgres attach` command is designed for sync database drivers that accept `?sslmode=disable`. However, async drivers like `asyncpg` use different SSL configuration:

- **Sync drivers (psycopg2)**: `postgres://user:pass@host:port/db?sslmode=disable`
- **Async drivers (asyncpg)**: `postgresql+asyncpg://user:pass@host:port/db` (SSL via separate parameter)

Our backend uses async SQLAlchemy with asyncpg for better performance, which is why we hit this incompatibility.
