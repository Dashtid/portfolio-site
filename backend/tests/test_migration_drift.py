"""
D3-BE-04: the migration chain must produce exactly the model schema.

Production's schema is owned by Alembic (fly.toml release_command);
create_all no longer runs there. That means any model edit that ships
without a migration would silently never reach prod — SELECTs naming the
new column would 500 while every test (running on create_all) stayed
green. This test closes that gap: upgrade an EMPTY database to head,
then autogenerate-compare it against Base.metadata and demand zero diffs.

Runs on SQLite. Type rendering differs between dialects, so the compare
uses Alembic's default type comparison (which normalises the common
cases); if a future diff is provably dialect noise rather than real
drift, filter it explicitly here with a comment — do not loosen the
assertion wholesale.
"""

import os
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

# Import every model so Base.metadata is fully populated.
import app.models  # noqa: F401
from alembic import command  # type: ignore[attr-defined]
from app.database import Base

_BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def empty_db_at_head(tmp_path):
    """Yield a sync SQLAlchemy engine for an empty DB migrated to head."""
    db_path = tmp_path / "drift-check.db"
    async_url = f"sqlite+aiosqlite:///{db_path}"

    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))

    # env.py honours ALEMBIC_DATABASE_URL over the settings singleton.
    os.environ["ALEMBIC_DATABASE_URL"] = async_url
    try:
        command.upgrade(config, "head")
    finally:
        os.environ.pop("ALEMBIC_DATABASE_URL", None)

    engine = create_engine(f"sqlite:///{db_path}")
    yield engine
    engine.dispose()


def test_upgrade_from_empty_matches_models(empty_db_at_head):
    with empty_db_at_head.connect() as connection:
        context = MigrationContext.configure(connection)
        diffs = compare_metadata(context, Base.metadata)

    assert diffs == [], (
        "Migration chain and models disagree — a model was edited without "
        f"a migration (or vice versa). Autogenerate diff:\n{diffs}"
    )


def test_baseline_created_page_views_city(empty_db_at_head):
    """The column whose absence motivated D3-BE-04 must exist at head."""
    from sqlalchemy import inspect

    columns = {col["name"] for col in inspect(empty_db_at_head).get_columns("page_views")}
    assert "city" in columns
