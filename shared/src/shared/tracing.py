"""OpenTelemetry, kept optional.

Tracing is off unless `OTEL_EXPORTER_OTLP_ENDPOINT` is set, and the `otel`
extra may not be installed at all, so every helper here degrades to a no-op
rather than forcing the dependency on services that do not want it.
"""

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

try:
    from opentelemetry import propagate, trace
    from opentelemetry.trace import SpanKind

    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on the `otel` extra
    _OTEL_AVAILABLE = False

_TRACEPARENT = "traceparent"


def setup_tracing(service_name: str) -> None:
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logging.info("OTEL_EXPORTER_OTLP_ENDPOINT unset, tracing disabled")
        return
    if not _OTEL_AVAILABLE:
        logging.warning("Tracing requested but the `otel` extra is not installed")
        return

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    PymongoInstrumentor().instrument()
    RedisInstrumentor().instrument()
    logging.info("Tracing enabled for `%s` exporting to %s", service_name, endpoint)


def instrument_app(app: Any) -> None:
    """Instrument a FastAPI app, if tracing is on."""
    if not (_OTEL_AVAILABLE and os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")):
        return
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)


def current_traceparent() -> str:
    """W3C trace context for the active span, or "" when tracing is off."""
    if not _OTEL_AVAILABLE:
        return ""
    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    return carrier.get(_TRACEPARENT, "")


@contextmanager
def consumer_span(name: str, traceparent: str, **attributes: str) -> Iterator[None]:
    """Continue the producer's trace while handling a message.

    Without this each service produces its own disconnected trace: the stream
    is an async boundary that automatic instrumentation cannot see across.
    """
    if not _OTEL_AVAILABLE:
        yield
        return

    parent = propagate.extract({_TRACEPARENT: traceparent}) if traceparent else None
    tracer = trace.get_tracer("shared.redis.consumer")
    with tracer.start_as_current_span(name, context=parent, kind=SpanKind.CONSUMER) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield
