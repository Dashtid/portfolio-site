"""The production uvicorn command line, parsed the way uvicorn parses it.

TestClient never starts uvicorn, so nothing else in the suite sees these
flags: a regression in the image's CMD would pass every other test.
"""

import json
import re
from pathlib import Path
from typing import Any

from uvicorn.main import main as uvicorn_cli

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"


def _cmd() -> list[str]:
    """The exec-form CMD array of the final stage, line continuations joined."""
    text = re.sub(r"\\\r?\n", " ", DOCKERFILE.read_text(encoding="utf-8"))
    cmds = [line for line in text.splitlines() if line.startswith("CMD [")]
    return json.loads(cmds[-1].removeprefix("CMD "))


def _uvicorn_params() -> dict[str, Any]:
    cmd = _cmd()
    assert cmd[:4] == ["python", "-m", "uvicorn", "app.main:app"]
    return uvicorn_cli.make_context("uvicorn", cmd[3:]).params


def test_proxy_headers_are_off() -> None:
    """uvicorn must not take the client address or scheme from forwarding headers.

    With proxy headers on and every peer trusted, request.client became the
    leftmost X-Forwarded-For entry, which Fly's proxy passes through from the
    client. uvicorn turns proxy headers on by default, so the flag is explicit.
    """
    assert _uvicorn_params()["proxy_headers"] is False
