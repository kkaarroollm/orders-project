from typing import ClassVar

from shared.events.base import DeliveryEvent, OrderEvent, SimulationRequest

DELIVERIES_STREAM = "deliveries-stream"
SIMULATE_DELIVERY_STREAM = "simulate-delivery-stream"
DELIVERY_STATUS_STREAM = "delivery-status-stream"


class DeliveryCreated(DeliveryEvent):
    stream: ClassVar[str] = DELIVERIES_STREAM
    event_type: ClassVar[str] = "delivery.created.v1"
    legacy_types: ClassVar[tuple[str, ...]] = ("delivery.created",)


class DeliveryStatusChanged(DeliveryEvent):
    stream: ClassVar[str] = DELIVERIES_STREAM
    event_type: ClassVar[str] = "delivery.status_updated.v1"
    legacy_types: ClassVar[tuple[str, ...]] = ("delivery.status_updated",)


class DeliverySimulationRequested(SimulationRequest):
    stream: ClassVar[str] = SIMULATE_DELIVERY_STREAM
    event_type: ClassVar[str] = "delivery.simulate.v1"
    legacy_types: ClassVar[tuple[str, ...]] = ("delivery.simulate",)


class DeliveryStatusSimulated(OrderEvent):
    """Carries the *order* id: the simulator only ever knows the order it drives."""

    stream: ClassVar[str] = DELIVERY_STATUS_STREAM
    event_type: ClassVar[str] = "delivery.status_simulated.v1"
    legacy_types: ClassVar[tuple[str, ...]] = ("delivery.status_simulated",)
