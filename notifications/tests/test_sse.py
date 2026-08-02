import asyncio
import json

import pytest

from src.sse import OrderStreamRegistry, event_stream, format_event


@pytest.fixture
def registry():
    return OrderStreamRegistry()


async def _next(stream) -> str:
    return await asyncio.wait_for(anext(stream), timeout=1)


def test_format_event_uses_sse_framing():
    frame = format_event({"order_id": "order123", "status": "preparing", "timestamp": "2026-08-02T10:00:00Z"})

    assert frame.startswith("id: 2026-08-02T10:00:00Z\ndata: ")
    assert frame.endswith("\n\n")
    assert json.loads(frame.split("data: ", 1)[1].strip())["status"] == "preparing"


@pytest.mark.asyncio
async def test_stream_opens_with_retry_then_snapshot(registry):
    snapshot = {"order_id": "order123", "status": "confirmed", "timestamp": "t0"}
    stream = event_stream(registry, "order123", snapshot)

    retry = await _next(stream)
    assert retry.startswith("retry: ")

    first = await _next(stream)
    assert json.loads(first.split("data: ", 1)[1].strip())["status"] == "confirmed"

    await stream.aclose()


@pytest.mark.asyncio
async def test_broadcast_reaches_an_open_stream(registry):
    stream = event_stream(registry, "order123", None)
    await _next(stream)  # retry line; subscribes on first pull

    await registry.broadcast("order123", {"order_id": "order123", "status": "preparing", "timestamp": "t1"})

    frame = await _next(stream)
    assert json.loads(frame.split("data: ", 1)[1].strip())["status"] == "preparing"

    await stream.aclose()


@pytest.mark.asyncio
async def test_close_all_ends_open_streams(registry):
    """Shutdown must end the response so clients reconnect to a healthy pod."""
    stream = event_stream(registry, "order123", None)
    await _next(stream)

    await registry.close_all()

    with pytest.raises(StopAsyncIteration):
        await _next(stream)


@pytest.mark.asyncio
async def test_unsubscribes_when_client_disconnects(registry):
    stream = event_stream(registry, "order123", None)
    await _next(stream)
    assert registry._subscribers["order123"]

    await stream.aclose()

    assert "order123" not in registry._subscribers
