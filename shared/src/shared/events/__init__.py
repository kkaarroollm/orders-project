from shared.events.base import DeliveryEvent, DomainEvent, OrderEvent, SimulationRequest
from shared.events.delivery import (
    DeliveryCreated,
    DeliverySimulationRequested,
    DeliveryStatusChanged,
    DeliveryStatusSimulated,
)
from shared.events.notifications import OrderStatusPush
from shared.events.order import (
    OrderCreated,
    OrderSimulationRequested,
    OrderStatusChanged,
    OrderStatusSimulated,
)

ALL_EVENTS: tuple[type[DomainEvent], ...] = (
    OrderCreated,
    OrderStatusChanged,
    OrderSimulationRequested,
    OrderStatusSimulated,
    DeliveryCreated,
    DeliveryStatusChanged,
    DeliverySimulationRequested,
    DeliveryStatusSimulated,
    OrderStatusPush,
)

EVENT_REGISTRY: dict[str, type[DomainEvent]] = {}
for _event in ALL_EVENTS:
    for _wire_type in (_event.event_type, *_event.legacy_types):
        if _wire_type in EVENT_REGISTRY:
            raise RuntimeError(f"Duplicate event type `{_wire_type}` on {_event.__name__}")
        EVENT_REGISTRY[_wire_type] = _event

__all__ = [
    "ALL_EVENTS",
    "EVENT_REGISTRY",
    "DeliveryCreated",
    "DeliveryEvent",
    "DeliverySimulationRequested",
    "DeliveryStatusChanged",
    "DeliveryStatusSimulated",
    "DomainEvent",
    "OrderCreated",
    "OrderEvent",
    "OrderSimulationRequested",
    "OrderStatusChanged",
    "OrderStatusPush",
    "OrderStatusSimulated",
    "SimulationRequest",
]
