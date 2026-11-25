"""
BodySizeLimitMiddleware's streaming counter, driven the way uvicorn drives it.

A body without a Content-Length is counted as it arrives. Past the cap the
middleware hands downstream an empty terminal frame (more_body=False) and
answers 413, unless the response is already under way. A body that arrives
too slowly is cut off the same way and answered 408. After that frame
ASGI allows only http.disconnect, so anything still listening must get
exactly that, however much body is in flight. starlette 1.8's FileResponse
listens while it streams below ASGI 2.4, and uvicorn speaks 2.3.

TestClient cannot reach this path: it delivers the whole body as one
message, so nothing is in flight once the cap is passed. These tests speak
raw ASGI instead.
"""

import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.types import Message, Receive, Scope, Send

from app.main import BODY_SIZE_CAPS, MAX_BODY_SIZE, BodySizeLimitMiddleware, app

MB = 1024 * 1024
THESIS = Path(__file__).resolve().parents[1] / "static" / "documents" / "bachelor-thesis.pdf"

# In 1 MB chunks, the cap is passed with one more chunk still in flight.
CHUNKS_PAST_THE_CAP = MAX_BODY_SIZE // MB + 2


def _chunked_scope(method: str, path: str) -> dict[str, Any]:
    """An HTTP scope as uvicorn builds it for a chunked request."""
    return _scope(method, path, (b"transfer-encoding", b"chunked"))


def _sized_scope(method: str, path: str, length: int) -> dict[str, Any]:
    """An HTTP scope as uvicorn builds it for a request with a Content-Length."""
    return _scope(method, path, (b"content-length", str(length).encode()))


def _scope(method: str, path: str, framing: tuple[bytes, bytes]) -> dict[str, Any]:
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": [(b"host", b"testserver"), framing],
        "client": ("198.51.100.7", 50000),
        "server": ("testserver", 80),
    }


class ChunkedClient:
    """The client side of one request, as uvicorn presents it to the app.

    receive() hands out the chunks as http.request messages, the last one
    with more_body=False, then reports http.disconnect: at once when the
    client hangs up after its body, otherwise once the response is complete.
    With body_after_response_start the chunks only arrive once the response
    has started; over a real connection FileResponse starts long before 5 MB
    can arrive. send() records the response.
    """

    def __init__(
        self,
        chunks: list[bytes],
        *,
        hangs_up: bool = False,
        body_after_response_start: bool = False,
    ) -> None:
        self.chunks = chunks
        self.handed_out = 0
        self.hangs_up = hangs_up
        self.body_after_response_start = body_after_response_start
        self.status: int | None = None
        self.headers: dict[str, str] = {}
        self.body = bytearray()
        self.response_started = asyncio.Event()
        self.response_complete = asyncio.Event()

    async def receive(self) -> Message:
        if self.body_after_response_start:
            await self.response_started.wait()
        if self.handed_out < len(self.chunks):
            self.handed_out += 1
            return {
                "type": "http.request",
                "body": self.chunks[self.handed_out - 1],
                "more_body": self.handed_out < len(self.chunks),
            }
        if not self.hangs_up:
            await self.response_complete.wait()
        return {"type": "http.disconnect"}

    async def send(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            self.status = message["status"]
            self.headers = {k.decode().lower(): v.decode() for k, v in message["headers"]}
            self.response_started.set()
        elif message["type"] == "http.response.body":
            self.body += message.get("body", b"")
            if not message.get("more_body", False):
                self.response_complete.set()


class PacedClient(ChunkedClient):
    """A ChunkedClient that waits `interval` seconds before each chunk.

    With `stalls`, every chunk claims more is coming and none ever does:
    after the last one, receive() waits for the response to complete.
    """

    def __init__(self, chunks: list[bytes], *, interval: float, stalls: bool = False) -> None:
        super().__init__(chunks)
        self.interval = interval
        self.stalls = stalls

    async def receive(self) -> Message:
        if self.handed_out < len(self.chunks):
            await asyncio.sleep(self.interval)
            message = await super().receive()
            if self.stalls:
                message["more_body"] = True
            return message
        return await super().receive()


class TestChunkedBodyPastTheCap:
    """After its terminal frame the middleware passes on only the disconnect."""

    @pytest.mark.asyncio
    async def test_next_receive_after_the_terminal_frame_is_the_disconnect(self):
        """7 MB in 1 MB chunks, then the client hangs up.

        Downstream reads to the terminal frame and asks once more, as a
        disconnect listener does. The chunk still in flight must be read and
        dropped, not handed out as a second http.request.
        """
        received: list[Message] = []

        async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
            while True:
                message = await receive()
                received.append(message)
                if not message.get("more_body", False):
                    break
            received.append(await receive())
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"handler ran"})

        client = ChunkedClient([b"x" * MB] * CHUNKS_PAST_THE_CAP, hangs_up=True)
        async with asyncio.timeout(10):
            await BodySizeLimitMiddleware(downstream)(
                _chunked_scope("POST", "/api/v1/probe"), client.receive, client.send
            )

        assert client.status == 413
        *frames, after_terminal_frame = received
        assert frames[-1] == {"type": "http.request", "body": b"", "more_body": False}
        assert sum(len(frame["body"]) for frame in frames) <= MAX_BODY_SIZE
        assert after_terminal_frame == {"type": "http.disconnect"}
        assert client.handed_out == CHUNKS_PAST_THE_CAP

    @pytest.mark.asyncio
    async def test_static_get_with_a_chunked_body_past_the_cap_serves_the_whole_file(self):
        """GET a static PDF while 7 MB of chunked body streams in.

        The file must arrive whole and the app must raise nothing. Without
        the drain, on starlette 1.8, FileResponse's disconnect listener got
        the chunk after the terminal frame, BaseHTTPMiddleware raised, and
        the file was cut off under its full Content-Length.
        """
        expected = THESIS.read_bytes()
        client = ChunkedClient([b"q" * MB] * CHUNKS_PAST_THE_CAP, body_after_response_start=True)

        async with asyncio.timeout(30):
            await app(
                _chunked_scope("GET", "/static/documents/bachelor-thesis.pdf"),
                client.receive,
                client.send,
            )

        assert client.status == 200
        assert client.headers["content-length"] == str(len(expected))
        assert bytes(client.body) == expected


class TestDownstreamValueError:
    """A ValueError raised below the middleware is not caught there."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("body", [b"", b'{"page_path": "/"}'], ids=["empty", "json"])
    async def test_propagates_after_a_single_dispatch(self, body: bytes):
        """pydantic's ValidationError and json's JSONDecodeError are ValueErrors.

        The Content-Length parse shared a try block with call_next, so one
        raised by the app was taken for an unparseable header and the
        request went through the app again.
        """
        dispatches = 0

        async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal dispatches
            dispatches += 1
            raise ValueError("raised by the app")

        client = ChunkedClient([body], hangs_up=True)
        with pytest.raises(ValueError, match="raised by the app"):
            await BodySizeLimitMiddleware(downstream)(
                _sized_scope("POST", "/api/v1/probe", len(body)), client.receive, client.send
            )

        assert dispatches == 1


class TestAnonymousJsonBodyCaps:
    """The routes that take an anonymous JSON body stop at 16 KB, not 5 MB."""

    PATHS = ["/api/v1/analytics/track/pageview", "/api/v1/auth/refresh"]

    def test_both_routes_are_capped_at_16_kb(self):
        assert {path: BODY_SIZE_CAPS[path] for path in self.PATHS} == dict.fromkeys(
            self.PATHS, 16 * 1024
        )

    @pytest.mark.parametrize("path", PATHS)
    def test_declared_body_past_the_cap_is_413(self, client: TestClient, path: str):
        response = client.post(
            path,
            content=b'{"page_path": "' + b"a" * (16 * 1024) + b'"}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 413
        assert response.json() == {"detail": "Request body too large. Maximum size is 16 KB."}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("path", PATHS)
    async def test_chunked_body_past_the_cap_is_413(self, path: str):
        """100 KB without a Content-Length: counted as it arrives, cut at 16 KB."""
        handed_down = 0

        async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal handed_down
            while True:
                message = await receive()
                handed_down += len(message.get("body", b""))
                if not message.get("more_body", False):
                    break
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"handler ran"})

        client = ChunkedClient([b"a" * 1024] * 100, hangs_up=True)
        async with asyncio.timeout(10):
            await BodySizeLimitMiddleware(downstream)(
                _chunked_scope("POST", path), client.receive, client.send
            )

        assert client.status == 413
        assert handed_down <= 16 * 1024

    def test_largest_schema_valid_beacon_fits(self, client: TestClient):
        """Every field at its schema maximum is still under the cap."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={
                "page_path": "/" + "p" * 2047,
                "page_title": "t" * 512,
                "referrer": "https://example.com/" + "r" * 2028,
                "visitor_id": "v" * 128,
            },
        )

        assert response.status_code == 200


async def _read_body_then_ok(scope: Scope, receive: Receive, send: Send) -> None:
    """Read the body to its terminal frame, then answer 200 with its length."""
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body", False):
            break
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": str(len(body)).encode()})


class TestBodyReadDeadline:
    """A body gets a grace period, then must keep up a floor rate, or it is a 408.

    Patched to 0.5 s and 1000 bytes a second so the tests run in seconds.
    """

    @pytest.fixture(autouse=True)
    def short_deadline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("app.main.BODY_READ_GRACE_SECONDS", 0.5)
        monkeypatch.setattr("app.main.BODY_READ_MIN_RATE", 1000)

    @pytest.mark.asyncio
    async def test_stalled_body_is_408_with_connection_close(self):
        """A beacon that declares 1000 bytes and sends 12, through the whole app.

        Without a deadline the request, and its connection, waited for the
        other 988 bytes for as long as the client kept the socket open.
        """
        client = PacedClient([b'{"page_path"'], interval=0, stalls=True)
        async with asyncio.timeout(10):
            await app(
                _sized_scope("POST", "/api/v1/analytics/track/pageview", 1000),
                client.receive,
                client.send,
            )

        assert client.status == 408
        assert client.headers["connection"] == "close"
        assert b"not received in time" in client.body

    @pytest.mark.asyncio
    async def test_body_above_the_floor_rate_is_read_whole(self):
        """2 s at 2000 bytes a second: past the grace period, never past the deadline."""
        client = PacedClient([b"a" * 200] * 20, interval=0.1)
        async with asyncio.timeout(10):
            await BodySizeLimitMiddleware(_read_body_then_ok)(
                _sized_scope("POST", "/api/v1/probe", 4000), client.receive, client.send
            )

        assert client.status == 200
        assert client.body == b"4000"

    @pytest.mark.asyncio
    async def test_body_below_the_floor_rate_is_cut_off(self):
        """10 bytes every 0.2 s is 50 bytes a second: cut off after the grace period."""
        client = PacedClient([b"a" * 10] * 20, interval=0.2)
        async with asyncio.timeout(10):
            await BodySizeLimitMiddleware(_read_body_then_ok)(
                _chunked_scope("POST", "/api/v1/probe"), client.receive, client.send
            )

        assert client.status == 408
        assert client.handed_out < 5

    @pytest.mark.asyncio
    async def test_waiting_for_the_disconnect_after_the_body_has_no_deadline(self):
        """Once the body is complete, a disconnect listener may wait past the deadline.

        A timed-out frame there would be an http.request after the terminal
        one, which BaseHTTPMiddleware raises on.
        """
        received: list[Message] = []

        async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
            received.append(await receive())
            received.append(await receive())
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"handler ran"})

        client = PacedClient([b"{}"], interval=0)
        disconnect_after = 1.0

        async def receive() -> Message:
            if client.handed_out:
                await asyncio.sleep(disconnect_after)
                return {"type": "http.disconnect"}
            return await client.receive()

        async with asyncio.timeout(10):
            await BodySizeLimitMiddleware(downstream)(
                _sized_scope("POST", "/api/v1/probe", 2), receive, client.send
            )

        assert received == [
            {"type": "http.request", "body": b"{}", "more_body": False},
            {"type": "http.disconnect"},
        ]
        assert client.status == 200


class TestUnreadBodyClosesTheConnection:
    """Through the whole app: a body not read to its end means Connection: close.

    uvicorn's keep-alive timer is cancelled by any byte that arrives after
    the response, so an unread body let a client hold the connection open.
    """

    BEACON = "/api/v1/analytics/track/pageview"

    @staticmethod
    async def _call(scope: dict[str, Any], client: ChunkedClient) -> None:
        async with asyncio.timeout(10):
            await app(scope, client.receive, client.send)

    @pytest.mark.asyncio
    async def test_get_with_a_declared_body_it_never_reads(self):
        """GET /api/v1/health declaring 16 bytes and sending none."""
        client = PacedClient([], interval=0, stalls=True)
        await self._call(_sized_scope("GET", "/api/v1/health", 16), client)

        assert client.status == 200
        assert client.headers["connection"] == "close"

    @pytest.mark.asyncio
    async def test_declared_size_past_the_cap(self):
        """A 413 answered from Content-Length alone, before any byte is read."""
        client = PacedClient([], interval=0, stalls=True)
        await self._call(_sized_scope("POST", self.BEACON, 17 * 1024), client)

        assert client.status == 413
        assert client.headers["connection"] == "close"

    @pytest.mark.asyncio
    async def test_chunked_body_cut_off_at_the_cap(self):
        client = ChunkedClient([b"a" * 1024] * 100, hangs_up=True)
        await self._call(_chunked_scope("POST", self.BEACON), client)

        assert client.status == 413
        assert client.headers["connection"] == "close"

    @pytest.mark.asyncio
    async def test_body_read_to_its_end_keeps_the_connection(self):
        """Malformed JSON is read in full before FastAPI's 422."""
        client = ChunkedClient([b"{"])
        await self._call(_sized_scope("POST", self.BEACON, 1), client)

        assert client.status == 422
        assert "connection" not in client.headers

    @pytest.mark.asyncio
    async def test_request_without_a_body_keeps_the_connection(self):
        client = ChunkedClient([b""])
        await self._call(_scope("GET", "/api/v1/health", (b"accept", b"*/*")), client)

        assert client.status == 200
        assert "connection" not in client.headers
