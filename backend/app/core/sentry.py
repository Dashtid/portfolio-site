"""
Sentry client options: what the SDK may collect, and the scrubbing hooks

main.py starts the client only when SENTRY_DSN is set. The SDK collects no
user data, cookies, request bodies, query strings, local variables or SQL
parameters, and sends request headers by allowlist. The hooks then filter
what still reaches an event, a transaction or a breadcrumb: values under
credential, cookie, client-address and query-string keys, and database URLs,
URL credentials and IP addresses inside any string.
"""

import ipaddress
import logging
import re
from collections.abc import Mapping
from typing import Any

from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import EventHandler, LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.config import settings

FILTERED = "[Filtered]"

# The security event log (app/core/security_events.py). LoggingIntegration
# sends its ERROR records as it does any logger's; attach_security_event_handler
# adds the WARNING records and the notices, so an alert rule on the logger
# tag app.security sees every refused or suspicious authentication decision.
SECURITY_LOGGER = "app.security"
# Events below WARNING that are sent all the same: each admin sign-in, so a
# sign-in nobody expected shows up in the alert mail.
SECURITY_NOTICES = frozenset({"auth.login_success"})

# Request headers sent with their values, matched as case-insensitive
# substrings; every other header keeps its name with a filtered value.
SENT_HEADERS = ["content-length", "content-type", "host", "user-agent"]

# Every category is named: a data_collection dict collects in full for any
# category it leaves out.
DATA_COLLECTION: dict[str, Any] = {
    "user_info": False,  # user.* fields and the client address
    "cookies": {"mode": "off"},
    "http_headers": {"request": {"mode": "allowlist", "terms": SENT_HEADERS}},
    "http_bodies": [],
    "url_query_params": {"mode": "off"},
    "database_query_data": False,  # SQL parameters
    "stack_frame_variables": False,  # locals hold request values and the DB password
    "frame_context_lines": 5,  # source lines around each frame; the code is public
    "graphql": {"document": False, "variables": False},
    "gen_ai": {"inputs": False, "outputs": False},
    "queues": False,
}

# Keys whose values are filtered at any depth, compared lowercased with "_"
# read as "-": the app's log extras and the httpx breadcrumbs use both.
_DENIED_KEYS = frozenset(
    {
        # credentials and session cookies
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "password",
        "passwd",
        "secret",
        "client-secret",
        "token",
        "access-token",
        "refresh-token",
        "session",
        "sessionid",
        "csrftoken",
        # client addresses and the keyed digest the logs carry for them
        "client-ip",
        "client-ip-hash",
        "ip",
        "ip-address",
        "remote-addr",
        "forwarded",
        "x-forwarded-for",
        "x-real-ip",
        "fly-client-ip",
        # query strings, raw or parsed
        "query-string",
        "query-params",
        "http.query",
        "http.fragment",
    }
)

# A database or cache URL, whole: user, password, host and database name.
_DATABASE_URL = re.compile(
    r"\b(?:postgres(?:ql)?|mysql|mariadb|sqlite|rediss?|amqps?|mongodb(?:\+srv)?)"
    r"(?:\+\w+)?://[^\s'\"<>]*",
    re.IGNORECASE,
)
# The user:password@ part of any other URL.
_URL_CREDENTIALS = re.compile(r"(?<=://)[^\s/@'\"<>]+@")
_IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
_IPV6 = re.compile(r"(?<![\w:.])(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(?![\w:.])", re.IGNORECASE)


def _filter_address(match: re.Match[str]) -> str:
    """A matched IP address as FILTERED; loopback, unspecified and non-addresses stay."""
    text = match.group(0)
    try:
        address = ipaddress.ip_address(text)
    except ValueError:
        return text
    return text if address.is_loopback or address.is_unspecified else FILTERED


def _scrub_text(text: str) -> str:
    text = _DATABASE_URL.sub(FILTERED, text)
    text = _URL_CREDENTIALS.sub(f"{FILTERED}@", text)
    text = _IPV4.sub(_filter_address, text)
    return _IPV6.sub(_filter_address, text)


def _denied(key: object) -> bool:
    return isinstance(key, str) and key.lower().replace("_", "-") in _DENIED_KEYS


def _scrub(value: Any) -> Any:
    """`value` with denied keys' values filtered and every string scrubbed."""
    if isinstance(value, str):
        return _scrub_text(value)
    if isinstance(value, dict):
        return {key: FILTERED if _denied(key) else _scrub(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    return value


def scrub_event(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    """before_send and before_send_transaction: the event without request
    bodies, cookies, query strings or client addresses, then scrubbed.

    A hook that raises drops the event, so a failure here never sends it
    unscrubbed.
    """
    _ = hint
    request = event.get("request")
    if isinstance(request, dict):
        for part in ("cookies", "data", "env", "query_string"):
            request.pop(part, None)
    # _meta holds the serializer's annotations (lengths and removal
    # reasons), not values, and must keep its shape.
    meta = event.pop("_meta", None)
    scrubbed: dict[str, Any] = _scrub(event)
    if meta is not None:
        scrubbed["_meta"] = meta
    return scrubbed


def scrub_breadcrumb(crumb: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    """before_breadcrumb: the breadcrumb, scrubbed before the scope stores it."""
    _ = hint
    scrubbed: dict[str, Any] = _scrub(crumb)
    return scrubbed


# Request paths whose transactions are never sampled: the page-view beacon,
# sent for every page a visitor opens, and the health checks.
UNSAMPLED_PATH_PREFIXES = ("/api/v1/analytics/track/pageview", "/api/v1/health")


def traces_sampler(sampling_context: dict[str, Any]) -> float:
    """traces_sampler: the sample rate of one request's transaction.

    The ASGI integration passes the request's ASGI scope as asgi_scope, and
    the sampled flag of an incoming sentry-trace header as parent_sampled
    (None without one). The page-view beacon and the health checks get 0.0.
    Any other request follows the parent decision, 1.0 or 0.0, as the SDK
    does when no sampler is set, and without one gets
    SENTRY_TRACES_SAMPLE_RATE.
    """
    asgi_scope = sampling_context.get("asgi_scope")
    path = asgi_scope.get("path") if isinstance(asgi_scope, Mapping) else None
    if isinstance(path, str) and path.startswith(UNSAMPLED_PATH_PREFIXES):
        return 0.0
    parent_sampled = sampling_context.get("parent_sampled")
    if parent_sampled is not None:
        return 1.0 if parent_sampled else 0.0
    return settings.SENTRY_TRACES_SAMPLE_RATE


class SecurityEventFilter(logging.Filter):
    """Passes the security records LoggingIntegration does not send itself:
    WARNING ones, and SECURITY_NOTICES below WARNING. ERROR and above stay
    with the integration, which would otherwise send each of them twice."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.ERROR:
            return False
        if record.levelno >= logging.WARNING:
            return True
        return getattr(record, "event", None) in SECURITY_NOTICES


def attach_security_event_handler() -> None:
    """Send the app.security records SecurityEventFilter passes as Sentry
    events, through the same before_send scrubbing as every other event.

    Call it after sentry_sdk.init. The logger is set up first, because
    get_logger leaves a logger that already has a handler unconfigured; a
    second call adds nothing.
    """
    from app.utils.logger import get_logger  # noqa: PLC0415

    security_logger = get_logger(SECURITY_LOGGER)
    if any(isinstance(handler, EventHandler) for handler in security_logger.handlers):
        return
    handler = EventHandler(level=logging.INFO)
    handler.addFilter(SecurityEventFilter())
    security_logger.addHandler(handler)


def sentry_options() -> dict[str, Any]:
    """Keyword arguments for sentry_sdk.init.

    Integrations are enumerated rather than left to Sentry's auto-enable,
    so the set is visible in review and stable across SDK versions:
    SqlalchemyIntegration adds a span per query, HttpxIntegration covers the
    outbound GitHub API calls, and AsyncioIntegration links the contexts of
    tasks spawned with asyncio.create_task. LoggingIntegration keeps INFO
    and up as breadcrumbs and sends ERROR and up as events. traces_sampler
    decides every transaction's sample rate, SENTRY_TRACES_SAMPLE_RATE
    included, so traces_sample_rate is not passed.
    """
    return {
        "dsn": settings.SENTRY_DSN,
        "environment": settings.ENVIRONMENT,
        "release": f"portfolio-api@{settings.APP_VERSION}",
        "traces_sampler": traces_sampler,
        "profiles_sample_rate": settings.SENTRY_PROFILES_SAMPLE_RATE,
        "data_collection": DATA_COLLECTION,
        # The SDK reads a request body before data_collection decides not to
        # attach it; "never" keeps it from reading one at all.
        "max_request_body_size": "never",
        "before_send": scrub_event,
        "before_send_transaction": scrub_event,
        "before_breadcrumb": scrub_breadcrumb,
        "integrations": [
            StarletteIntegration(),
            FastApiIntegration(),
            SqlalchemyIntegration(),
            HttpxIntegration(),
            AsyncioIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
    }
