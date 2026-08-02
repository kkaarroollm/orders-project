from typing import ClassVar

from shared.events.base import DomainEvent

WS_EVENTS_STREAM = "ws-events"


class OrderStatusPush(DomainEvent):
    """A status update fanned out to every notifications replica.

    The domain streams use one shared consumer group, so exactly one replica
    receives each event -- but the client's stream may be held by any replica.
    This stream is consumed by a group *per replica* so all of them see it.
    """

    stream: ClassVar[str] = WS_EVENTS_STREAM
    event_type: ClassVar[str] = "order.status_push.v1"

    order_id: str
    status: str
    timestamp: str = ""
