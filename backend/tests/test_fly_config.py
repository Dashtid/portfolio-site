"""Fly's proxy settings in backend/fly.toml, which nothing else in the suite reads."""

import tomllib
from pathlib import Path

from app.main import BODY_READ_GRACE_SECONDS

FLY_TOML = Path(__file__).resolve().parents[1] / "fly.toml"


def test_connection_hard_limit_outlasts_held_requests() -> None:
    """At the hard limit Fly's proxy sends the machine no new traffic.

    A request whose body never arrives is held for BODY_READ_GRACE_SECONDS,
    so blocking the API takes hard_limit / grace new connections a second.
    At 25 that was 2.5, a rate one client sends without notice.
    """
    service = tomllib.loads(FLY_TOML.read_text(encoding="utf-8"))["http_service"]
    concurrency = service["concurrency"]

    assert concurrency["type"] == "connections"
    assert concurrency["hard_limit"] / BODY_READ_GRACE_SECONDS >= 25
