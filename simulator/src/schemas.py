from enum import Enum

from src.settings import settings


class SimulationStream(Enum):
    ORDER = (settings.simulate_order_stream, settings.order_status_stream)
    DELIVERY = (settings.simulate_delivery_stream, settings.delivery_status_stream)

    def __init__(self, source: str, target: str) -> None:
        self.source = source
        self.target = target


class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"


class DeliveryStatus(str, Enum):
    WAITING_FOR_PICKUP = "waiting_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
