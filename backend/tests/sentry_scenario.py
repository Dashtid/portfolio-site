"""Drive the API with the Sentry client on and save everything it would send.

tests/test_sentry_privacy.py runs this in a child process: the SDK patches
Starlette, FastAPI, SQLAlchemy, httpx and logging for the life of the
process, and it has to start before app.main includes its routers, as it
does in production. A capture transport keeps every envelope item; the
client gets the production options with a placeholder DSN, the transport
and every transaction sampled, and the security event handler is attached
as main.py attaches it.

Usage: python -m tests.sentry_scenario <output.json>
"""

import json
import sys
import warnings
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import sentry_sdk
from sentry_sdk.transport import Transport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.sentry import attach_security_event_handler, sentry_options
from app.utils.logger import get_logger

CLIENT_ADDRESS = "198.51.100.73"

# Values the requests carry. None of them may reach a captured payload.
MARKERS = {
    "email": "probe.contact@mail.example",
    "phone": "+46700000017",
    "personnummer": "19990101-0017",
    "db_pass": "dbpw-probe-5d8f2c",
    "bearer": "bearer-probe-9a7e41",
    "access_cookie": "cookie-probe-41b3c2",
    "refresh_cookie": "refresh-probe-77c0d9",
    "oauth_code": "oauth-code-probe-1f2e3d",
    "oauth_state": "oauth-state-probe-3d4c5b",
    "query": "query-probe-8b1a6f",
    "page": "page-probe-2c9d0e",
    "visitor": "visitor-probe-6e5f4a",
    "ip_hash": "iphash-probe-0c1d2e",
    "fly_client_ip": "203.0.113.45",
    "forwarded_for": "192.0.2.61",
    "real_ip": "198.51.100.88",
    "lookup_ip": "203.0.113.0",
    "client_ip": CLIENT_ADDRESS,
}

HEADERS = {
    "Authorization": f"Bearer {MARKERS['bearer']}",
    "Cookie": (
        f"access_token={MARKERS['access_cookie']}; refresh_token={MARKERS['refresh_cookie']}"
    ),
    "Fly-Client-IP": MARKERS["fly_client_ip"],
    "X-Forwarded-For": MARKERS["forwarded_for"],
    "X-Real-IP": MARKERS["real_ip"],
    "Referer": f"https://dashti.se/admin?q={MARKERS['query']}",
}

# A route that does what a failing request can: call out over httpx with an
# address in the URL, log with client fields, and raise with a database URL.
SCENARIO_PATH = "/api/v1/sentry-scenario"


class CaptureTransport(Transport):
    """Keeps each envelope item as its type and payload text instead of sending it."""

    def __init__(self) -> None:
        super().__init__()
        self.items: list[dict[str, Any]] = []

    def capture_envelope(self, envelope) -> None:
        for item in envelope.items:
            self.items.append(
                {"type": item.type, "payload": item.get_bytes().decode("utf-8", "replace")}
            )


async def _scenario_route() -> None:
    def ipapi(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="SE")

    async with httpx.AsyncClient(transport=httpx.MockTransport(ipapi)) as client:
        await client.get(f"https://ipapi.co/{MARKERS['lookup_ip']}/country/?key={MARKERS['query']}")
    get_logger("app.scenario").warning(
        "Lookup done",
        extra={"client_ip": MARKERS["client_ip"], "client_ip_hash": MARKERS["ip_hash"]},
    )
    raise RuntimeError(
        f"cannot reach postgresql://portfolio:{MARKERS['db_pass']}@db.internal:5432/app"
        f" for {MARKERS['fly_client_ip']}"
    )


def main(out_path: str) -> None:
    transport = CaptureTransport()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        sentry_sdk.init(
            **{
                **sentry_options(),
                "dsn": "https://public@sentry.invalid/1",
                "transport": transport,
                "traces_sample_rate": 1.0,
            }
        )
        attach_security_event_handler()
    init_warnings = [f"{w.category.__name__}: {w.message}" for w in caught]

    from fastapi.testclient import TestClient

    from app.core.deps import get_current_admin_user
    from app.database import get_db
    from app.main import app

    app.add_api_route(SCENARIO_PATH, _scenario_route, methods=["GET"])
    app.dependency_overrides[get_current_admin_user] = lambda: SimpleNamespace(id="probe-admin")
    # Nothing listens on port 1: the profile save fails as it would in a
    # database outage, with the password in the engine's URL.
    unreachable = create_async_engine(
        f"postgresql+asyncpg://portfolio:{MARKERS['db_pass']}@127.0.0.1:1/portfolio"
    )

    async def unreachable_db():
        async with AsyncSession(unreachable) as session:
            yield session

    statuses: dict[str, int] = {}
    with TestClient(app, raise_server_exceptions=False, client=(CLIENT_ADDRESS, 50000)) as client:
        statuses["callback"] = client.get(
            "/api/v1/auth/github/callback",
            params={"code": MARKERS["oauth_code"], "state": MARKERS["oauth_state"]},
            headers=HEADERS,
        ).status_code
        statuses["pageview"] = client.post(
            "/api/v1/analytics/track/pageview",
            json={
                "page_path": f"/{MARKERS['page']}?utm_source={MARKERS['query']}",
                "page_title": MARKERS["page"],
                "referrer": f"https://referrer.example/?q={MARKERS['query']}",
                "visitor_id": MARKERS["visitor"],
            },
            headers=HEADERS,
        ).status_code
        statuses["scenario"] = client.get(
            SCENARIO_PATH,
            params={"code": MARKERS["oauth_code"], "state": MARKERS["oauth_state"]},
            headers=HEADERS,
        ).status_code
        app.dependency_overrides[get_db] = unreachable_db
        statuses["profile"] = client.put(
            "/api/v1/admin/cv/profile",
            params={"section": MARKERS["query"]},
            json={
                "name": "Probe",
                "email": MARKERS["email"],
                "phone": MARKERS["phone"],
                "personnummer": MARKERS["personnummer"],
            },
            headers=HEADERS,
        ).status_code
        app.dependency_overrides.pop(get_db)

    sentry_sdk.flush()
    sent = {"warnings": init_warnings, "statuses": statuses, "items": transport.items}
    Path(out_path).write_text(json.dumps(sent), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
