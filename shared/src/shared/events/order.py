from typing import ClassVar

from shared.events.base import OrderEvent, SimulationRequest

ORDERS_STREAM = "orders-stream"
SIMULATE_ORDER_STREAM = "simulate-order-stream"
ORDER_STATUS_STREAM = "order-status-stream"


class OrderCreated(OrderEvent):
    stream: ClassVar[str] = ORDERS_STREAM
    event_type: ClassVar[str] = "order.created.v1"
    legacy_types: ClassVar[tuple[str, ...]] = ("order.created",)


class OrderStatusChanged(OrderEvent):
    stream: ClassVar[str] = ORDERS_STREAM
    event_type: ClassVar[str] = "order.status_updated.v1"
    legacy_types: ClassVar[tuple[str, ...]] = ("order.status_updated",)


class OrderSimulationRequested(SimulationRequest):
    stream: ClassVar[str] = SIMULATE_ORDER_STREAM
    event_type: ClassVar[str] = "order.simulate.v1"
    legacy_types: ClassVar[tuple[str, ...]] = ("order.simulate",)


class OrderStatusSimulated(OrderEvent):
    stream: ClassVar[str] = ORDER_STATUS_STREAM
    event_type: ClassVar[str] = "order.status_simulated.v1"
    legacy_types: ClassVar[tuple[str, ...]] = ("order.status_simulated",)
