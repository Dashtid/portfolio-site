"""
What the backend Sentry client may send

app/core/sentry.py keeps cookies, credentials, query strings, request bodies,
client addresses and database URLs out of every event, transaction and
breadcrumb. The hooks are tested directly; the end-to-end tests run
tests/sentry_scenario.py in a child process, where the SDK wraps the real
app as it does in production, and look for every value the requests carried
in everything the client would have sent.
"""

import json
import logging
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from sentry_sdk.integrations.logging import EventHandler, LoggingIntegration

from app.core.sentry import (
    DATA_COLLECTION,
    FILTERED,
    SECURITY_LOGGER,
    SecurityEventFilter,
    attach_security_event_handler,
    scrub_breadcrumb,
    scrub_event,
    sentry_options,
)
from app.utils.ip_hash import hash_ip
from tests.sentry_scenario import CLIENT_ADDRESS, MARKERS, SCENARIO_PATH

_BACKEND = Path(__file__).resolve().parents[1]


class TestOptions:
    def test_the_sdk_collects_no_personal_data(self):
        options = sentry_options()
        assert options["data_collection"] is DATA_COLLECTION
        assert DATA_COLLECTION["user_info"] is False
        assert DATA_COLLECTION["cookies"] == {"mode": "off"}
        assert DATA_COLLECTION["url_query_params"] == {"mode": "off"}
        assert DATA_COLLECTION["http_bodies"] == []
        assert DATA_COLLECTION["stack_frame_variables"] is False
        assert DATA_COLLECTION["database_query_data"] is False
        assert DATA_COLLECTION["http_headers"]["request"]["mode"] == "allowlist"
        assert options["max_request_body_size"] == "never"

    def test_every_category_is_named(self):
        """The SDK collects in full for a category the dict leaves out, so a
        category a new SDK version adds has to be decided here."""
        from sentry_sdk.data_collection import _resolve_explicit

        assert set(DATA_COLLECTION) == set(_resolve_explicit({})) - {"provided_by_user"}

    def test_hooks_are_installed(self):
        options = sentry_options()
        assert options["before_send"] is scrub_event
        assert options["before_send_transaction"] is scrub_event
        assert options["before_breadcrumb"] is scrub_breadcrumb

    def test_logging_integration_is_enumerated(self):
        integrations = sentry_options()["integrations"]
        assert sum(isinstance(item, LoggingIntegration) for item in integrations) == 1

    def test_no_option_the_pinned_sdk_deprecates_or_ignores(self):
        """send_default_pii and enable_tracing warn on init; with data_collection
        set, event_scrubber is ignored and include_local_variables unused."""
        deprecated = {"send_default_pii", "enable_tracing", "event_scrubber"}
        assert not deprecated & sentry_options().keys()
        assert "include_local_variables" not in sentry_options()


class TestScrubEvent:
    def _event(self) -> dict[str, Any]:
        return {
            "request": {
                "url": "https://api.dashti.se/api/v1/admin/cv/profile",
                "method": "PUT",
                "query_string": "code=c0de",
                "data": {"email": "contact@mail.example"},
                "cookies": {"access_token": "t0ken"},
                "env": {"REMOTE_ADDR": "203.0.113.9"},
                "headers": {
                    "host": "api.dashti.se",
                    "fly-client-ip": "203.0.113.9",
                    "authorization": "Bearer t0ken",
                },
            },
            "extra": {
                "client_ip_hash": "d1g3st",
                "query_params": {"code": "c0de"},
                "path": "/api/v1/admin/cv/profile",
                "status_code": 500,
            },
            "exception": {
                "values": [
                    {
                        "type": "OSError",
                        "value": "postgresql+asyncpg://app:pw@db.internal:5432/app at 203.0.113.9",
                    }
                ]
            },
            "breadcrumbs": {
                "values": [
                    {
                        "category": "httplib",
                        "data": {
                            "url": "https://ipapi.co/203.0.113.0/country/",
                            "http.query": "k=v",
                        },
                    }
                ]
            },
            "_meta": {"request": {"headers": {"": {"len": 3}}}},
        }

    def test_request_keeps_url_method_and_allowed_headers(self):
        scrubbed = scrub_event(self._event(), {})
        assert scrubbed["request"] == {
            "url": "https://api.dashti.se/api/v1/admin/cv/profile",
            "method": "PUT",
            "headers": {
                "host": "api.dashti.se",
                "fly-client-ip": FILTERED,
                "authorization": FILTERED,
            },
        }

    def test_denied_keys_are_filtered_at_any_depth(self):
        scrubbed = scrub_event(self._event(), {})
        assert scrubbed["extra"] == {
            "client_ip_hash": FILTERED,
            "query_params": FILTERED,
            "path": "/api/v1/admin/cv/profile",
            "status_code": 500,
        }
        assert scrubbed["breadcrumbs"]["values"][0]["data"] == {
            "url": f"https://ipapi.co/{FILTERED}/country/",
            "http.query": FILTERED,
        }

    def test_strings_lose_database_urls_and_addresses(self):
        scrubbed = scrub_event(self._event(), {})
        assert scrubbed["exception"]["values"][0]["value"] == f"{FILTERED} at {FILTERED}"

    def test_meta_annotations_keep_their_shape(self):
        scrubbed = scrub_event(self._event(), {})
        assert scrubbed["_meta"] == {"request": {"headers": {"": {"len": 3}}}}


class TestScrubBreadcrumb:
    def test_denied_keys_match_with_either_separator_and_any_case(self):
        crumb = {
            "category": "app.security",
            "data": {
                "client_ip": "a",
                "Fly-Client-IP": "b",
                "x_forwarded_for": "c",
                "user_id": "u",
            },
        }
        assert scrub_breadcrumb(crumb, {})["data"] == {
            "client_ip": FILTERED,
            "Fly-Client-IP": FILTERED,
            "x_forwarded_for": FILTERED,
            "user_id": "u",
        }

    def test_values_that_are_not_text_pass_unchanged(self):
        crumb = {"data": {"status_code": 500, "ok": False, "items": (1, 2)}, "timestamp": None}
        assert scrub_breadcrumb(crumb, {}) == {
            "data": {"status_code": 500, "ok": False, "items": [1, 2]},
            "timestamp": None,
        }

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("postgres://u:p@h:5432/db", FILTERED),
            ("redis://:secret@cache:6379/0 is down", f"{FILTERED} is down"),
            ("'sqlite+aiosqlite:///./portfolio.db'", f"'{FILTERED}'"),
            ("https://user:pass@example.com/x", f"https://{FILTERED}@example.com/x"),
            ("peer 2001:db8::7 reset", f"peer {FILTERED} reset"),
            ("https://[2001:db8::7]:443/", f"https://[{FILTERED}]:443/"),
            ("from 198.51.100.7, port 443", f"from {FILTERED}, port 443"),
        ],
    )
    def test_secrets_and_addresses_leave_message_text(self, text: str, expected: str):
        assert scrub_breadcrumb({"message": text}, {}) == {"message": expected}

    @pytest.mark.parametrize(
        "text",
        [
            "loopback 127.0.0.1, ::1 and 0.0.0.0 stay",
            "at 12:30:45 on 2026-11-25T03:15:00+00:00",
            "versions 1.65.1 and 10.0.26300",
            "999.1.1.1 is not an address",
            "https://api.github.com/users/x/repos",
        ],
    )
    def test_text_without_addresses_is_unchanged(self, text: str):
        assert scrub_breadcrumb({"message": text}, {}) == {"message": text}


def _security_record(level: int, event: str | None) -> logging.LogRecord:
    record = logging.LogRecord(SECURITY_LOGGER, level, __file__, 1, event or "x", None, None)
    if event is not None:
        record.event = event
    return record


class TestSecurityEvents:
    @pytest.mark.parametrize(
        ("level", "event", "passes"),
        [
            (logging.WARNING, "auth.login_refused", True),
            (logging.WARNING, "admin.metrics_reset", True),
            # LoggingIntegration sends these itself; passing them would send two.
            (logging.ERROR, "auth.refresh_cross_user", False),
            (logging.CRITICAL, "auth.refresh_cross_user", False),
            # The sign-in notice.
            (logging.INFO, "auth.login_success", True),
            (logging.INFO, "auth.logout", False),
            (logging.INFO, "auth.refresh_superseded", False),
            (logging.INFO, None, False),
        ],
    )
    def test_the_filter_passes_what_the_integration_does_not_send(
        self, level: int, event: str | None, passes: bool
    ):
        assert SecurityEventFilter().filter(_security_record(level, event)) is passes

    def test_the_handler_is_attached_once(self):
        security_logger = logging.getLogger(SECURITY_LOGGER)
        before = list(security_logger.handlers)
        try:
            attach_security_event_handler()
            attach_security_event_handler()
            added = [handler for handler in security_logger.handlers if handler not in before]
            assert len(added) == 1
            assert isinstance(added[0], EventHandler)
            assert any(isinstance(item, SecurityEventFilter) for item in added[0].filters)
            # The logger keeps its own stdout handler.
            assert any(
                not isinstance(handler, EventHandler) for handler in security_logger.handlers
            )
        finally:
            for handler in list(security_logger.handlers):
                if handler not in before:
                    security_logger.removeHandler(handler)


@pytest.fixture(scope="module")
def sent(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Everything the client captured while the scenario drove the app."""
    work = tmp_path_factory.mktemp("sentry")
    out = work / "sent.json"
    env = {
        **os.environ,
        # main.py must not start a second client: the scenario starts its own.
        "SENTRY_DSN": "",
        "DATABASE_URL": f"sqlite+aiosqlite:///{(work / 'app.db').as_posix()}",
        "UPLOAD_DIR": str(work / "uploads"),
    }
    for name in ("ENVIRONMENT", "FLY_APP_NAME"):
        env.pop(name, None)
    proc = subprocess.run(
        [sys.executable, "-m", "tests.sentry_scenario", str(out)],
        cwd=_BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-4000:]
    result: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
    return result


def _payloads(sent: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [json.loads(item["payload"]) for item in sent["items"] if item["type"] == kind]


def _frames(event: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for value in event.get("exception", {}).get("values", []):
        yield from (value.get("stacktrace") or {}).get("frames", [])


class TestWhatTheClientSends:
    def test_the_scenario_ran(self, sent: dict[str, Any]):
        assert sent["statuses"] == {
            "callback": 400,
            "pageview": 204,
            "scenario": 500,
            "profile": 500,
        }

    def test_no_request_value_reaches_a_payload(self, sent: dict[str, Any]):
        values = {**MARKERS, "client_ip_hash": hash_ip(CLIENT_ADDRESS)}
        leaks = [
            f"{name} in a {item['type']} item"
            for item in sent["items"]
            for name, value in values.items()
            if value in item["payload"]
        ]
        assert not leaks

    def test_errors_and_transactions_are_still_sent(self, sent: dict[str, Any]):
        transactions = {event["transaction"] for event in _payloads(sent, "transaction")}
        assert {
            "/api/v1/auth/github/callback",
            "/api/v1/analytics/track/pageview",
            "/api/v1/admin/cv/profile",
            SCENARIO_PATH,
        } <= transactions
        errors = _payloads(sent, "event")
        values = [v.get("value") for e in errors for v in e.get("exception", {}).get("values", [])]
        assert f"cannot reach {FILTERED} for {FILTERED}" in values
        urls = [e.get("request", {}).get("url", "") for e in errors]
        assert any(url.endswith("/api/v1/admin/cv/profile") for url in urls)

    def test_requests_carry_no_cookies_bodies_query_strings_or_addresses(
        self, sent: dict[str, Any]
    ):
        events = _payloads(sent, "event") + _payloads(sent, "transaction")
        with_request = [event for event in events if "request" in event]
        assert len(with_request) >= 4
        for event in with_request:
            request = event["request"]
            assert set(request) <= {"url", "method", "headers"}
            assert request["headers"]["host"] == "testserver"
            for header in ("authorization", "cookie", "fly-client-ip", "x-forwarded-for"):
                assert request["headers"][header] == FILTERED
            assert all("vars" not in frame for frame in _frames(event))

    def test_outgoing_request_breadcrumbs_keep_the_host_only(self, sent: dict[str, Any]):
        crumbs = [
            crumb
            for event in _payloads(sent, "event")
            for crumb in event.get("breadcrumbs", {}).get("values", [])
            if crumb.get("category") == "httplib"
        ]
        assert crumbs
        for crumb in crumbs:
            assert crumb["data"]["url"] == f"https://ipapi.co/{FILTERED}/country/"
            assert crumb["data"]["http.query"] == FILTERED

    def test_a_refused_oauth_state_is_sent_once_as_a_security_event(self, sent: dict[str, Any]):
        security = [e for e in _payloads(sent, "event") if e.get("logger") == SECURITY_LOGGER]
        assert [(e["level"], e["logentry"]["message"]) for e in security] == [
            ("warning", "auth.oauth_state_rejected")
        ]
        extra = security[0]["extra"]
        assert extra["event"] == "auth.oauth_state_rejected"
        assert extra["reason"] == "not_this_browser"
        assert extra["path"] == "/api/v1/auth/github/callback"

    def test_init_warns_about_no_pii_or_tracing_option(self, sent: dict[str, Any]):
        for warning in sent["warnings"]:
            for option in ("send_default_pii", "enable_tracing", "event_scrubber"):
                assert option not in warning
