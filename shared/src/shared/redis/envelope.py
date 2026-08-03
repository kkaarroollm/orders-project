from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class MessageEnvelope(BaseModel, Generic[T]):
    """Standard wrapper for all stream messages — enables tracing and debugging."""

    event_type: str
    correlation_id: str = ""
    source: str = ""
    # W3C trace context, so a consumer can continue the producer's trace across
    # the stream. Empty when tracing is off.
    traceparent: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
