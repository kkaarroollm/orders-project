from enum import Enum, auto


class SimulationStream(Enum):
    """Which simulation to run; the events themselves carry the stream names."""

    ORDER = auto()
    DELIVERY = auto()


class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"


class DeliveryStatus(str, Enum):
    WAITING_FOR_PICKUP = "waiting_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
