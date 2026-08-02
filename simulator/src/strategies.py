from dataclasses import dataclass

from shared.events.base import DomainEvent
from shared.events.delivery import DeliveryStatusSimulated
from shared.events.order import OrderStatusSimulated

from src.schemas import DeliveryStatus, OrderStatus, SimulationStream
from src.settings import settings


@dataclass(frozen=True)
class Step:
    delay_seconds: int
    status: str
    event: type[DomainEvent]


# Each simulation is a list of steps rather than a chain of sleeps: a step
# fires, publishes, and schedules the next one as a durable timer.
SIMULATION_STEPS: dict[SimulationStream, tuple[Step, ...]] = {
    SimulationStream.ORDER: (
        Step(settings.order_confirming_delay, OrderStatus.PREPARING.value, OrderStatusSimulated),
        Step(settings.order_preparing_delay, OrderStatus.OUT_FOR_DELIVERY.value, OrderStatusSimulated),
    ),
    SimulationStream.DELIVERY: (
        Step(settings.delivery_waiting_delay, DeliveryStatus.ON_THE_WAY.value, DeliveryStatusSimulated),
        Step(settings.delivery_way_delay, DeliveryStatus.DELIVERED.value, DeliveryStatusSimulated),
    ),
}
