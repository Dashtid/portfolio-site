"""Release-phase migration entrypoint (Fly release_command).

Replaces the bare `alembic upgrade head`, which crashed on any FRESH
database: the migration chain assumes the legacy pre-Alembic schema
exists (the root revision ALTERs page_views, later revisions ALTER
users, ...), so bootstrapping a new environment was impossible — the
release command failed and the deploy aborted.

Decision table (matches the root migration's documented intent):

- `alembic_version` table present -> normal `alembic upgrade head`.
- No tables at all (fresh DB)     -> `Base.metadata.create_all()` at
  current model spec, then `alembic stamp head` so future deploys
  upgrade incrementally from here.
- Tables but no `alembic_version` (legacy pre-Alembic DB) -> `alembic
  upgrade head`; the root revision syncs the drift and is guarded to
  tolerate partially-applied state.

Run from the backend directory: `python -m scripts.migrate`
"""

import asyncio
import sys
from pathlib import Path

from alembic.config import Config
from sqlalchemy import inspect

from alembic import command  # type: ignore[attr-defined]

# Ensure `app` is importable when invoked as a script from /app.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401, E402  (register every table on Base.metadata)
from app.database import Base, engine  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parent.parent


async def _prepare() -> str:
    """Inspect the DB and, for a fresh one, create the schema.

    Returns "stamp" when the schema was just created at current model
    spec (Alembic should only record head), otherwise "upgrade".
    """
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

        if "alembic_version" in tables:
            logger.info("Existing Alembic-managed database: upgrading to head")
            return "upgrade"

        if not tables:
            logger.info("Fresh database: creating schema at current model spec")
            await conn.run_sync(Base.metadata.create_all)
            return "stamp"

        logger.info(
            "Legacy database without alembic_version (%d tables): upgrading to head",
            len(tables),
        )
        return "upgrade"


def main() -> None:
    mode = asyncio.run(_prepare())
    asyncio.run(engine.dispose())

    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    # alembic.ini uses a path relative to the backend dir; pin it so the
    # script works regardless of the caller's cwd.
    config.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))

    if mode == "stamp":
        command.stamp(config, "head")
        logger.info("Stamped fresh database at head")
    else:
        command.upgrade(config, "head")
        logger.info("Upgraded database to head")


if __name__ == "__main__":
    main()
