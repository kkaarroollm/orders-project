import json
from unittest.mock import AsyncMock

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from shared.events.order import OrderCreated
from shared.redis.consumer import Route, StreamConsumer
from shared.redis.publisher import StreamProducer
from shared.tracing import consumer_span


# A TracerProvider can only be installed once per process, so it is set here
# rather than per test; each test just clears the exporter.
_EXPORTER = InMemorySpanExporter()
_PROVIDER = TracerProvider()
_PROVIDER.add_span_processor(SimpleSpanProcessor(_EXPORTER))
trace.set_tracer_provider(_PROVIDER)


@pytest.fixture
def spans():
    _EXPORTER.clear()
    return _EXPORTER


@pytest.mark.asyncio
async def test_publish_carries_trace_context(spans):
    redis = AsyncMock()
    producer: StreamProducer = StreamProducer(redis, source="orders-service")

    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("create order"):
        await producer.publish(OrderCreated(id="order123", status="confirmed"))

    envelope = json.loads(redis.xadd.call_args.args[1]["data"])
    assert envelope["traceparent"].startswith("00-")


@pytest.mark.asyncio
async def test_consumer_joins_the_producers_trace(spans):
    """Producer and consumer must land in one trace, not two disconnected ones."""
    redis = AsyncMock()
    producer: StreamProducer = StreamProducer(redis, source="orders-service")

    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("create order") as producer_span:
        expected_trace_id = producer_span.get_span_context().trace_id
        await producer.publish(OrderCreated(id="order123", status="confirmed"))

    envelope = json.loads(redis.xadd.call_args.args[1]["data"])
    with consumer_span("orders-stream process", envelope["traceparent"]):
        pass

    consumer = [span for span in spans.get_finished_spans() if span.name == "orders-stream process"]
    assert len(consumer) == 1
    assert consumer[0].context.trace_id == expected_trace_id


@pytest.mark.asyncio
async def test_handler_runs_inside_a_span(spans):
    redis = AsyncMock()
    handler = AsyncMock()
    consumer = StreamConsumer(
        redis=redis,
        stream="orders-stream",
        group="test-group",
        consumer_name="test",
        routes={OrderCreated.event_type: Route(OrderCreated, handler)},
    )
    message = {
        "data": json.dumps(
            {
                "event_type": OrderCreated.event_type,
                "correlation_id": "order123",
                "traceparent": "",
                "payload": {"id": "order123", "status": "confirmed"},
            }
        )
    }

    await consumer._process_message("1-1", message)

    handler.assert_awaited_once()
    names = [span.name for span in spans.get_finished_spans()]
    assert "orders-stream process" in names


def test_missing_traceparent_is_not_an_error(spans):
    """Tracing is optional, so an untraced message must still be handled."""
    with consumer_span("orders-stream process", ""):
        pass

    assert [span.name for span in spans.get_finished_spans()] == ["orders-stream process"]
