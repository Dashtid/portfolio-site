# Database

The backend uses **SQLAlchemy async** (`asyncpg` in production, `aiosqlite`
in development and tests) with Alembic-managed migrations.

## Configuration

The connection string lives in the `DATABASE_URL` environment variable
and falls back to a local SQLite file (`./portfolio.db`) when unset.

- **Production**: Fly Postgres app `dashti-portfolio-db`, attached to
  `dashti-portfolio-backend` via `flyctl postgres attach`. The attach
  command writes `DATABASE_URL` as a Fly secret and configures the
  internal-network DNS name.
- **Development**: SQLite default — no setup required beyond the first
  `uvicorn` run, which creates the file and applies migrations.
- **Tests**: a separate SQLite database (`./test.db`) defined in
  `backend/tests/conftest.py`. The test conftest also enables SQLite
  foreign-key enforcement so cascade-delete behaviour is covered.

The backend normalises `postgres://` URLs (Fly's default scheme) to
`postgresql+asyncpg://` automatically in `app/config.py`.

## Migrations

Alembic is initialised under `backend/alembic/` and runs from CI on every
backend deploy via `flyctl deploy`. Generate a new revision with:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Health Checks

`/api/v1/health/detailed` reports DB connectivity and the round-trip
latency of a `SELECT 1` probe — used by both Fly's `[[http_service.checks]]`
and the optional external uptime monitor.
