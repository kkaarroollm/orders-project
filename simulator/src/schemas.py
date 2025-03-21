from enum import Enum


class SimulationStream(Enum):
    """(listen_stream, send_stream)"""

    ORDER = ("simulate_order_stream", "order_status_stream")
    DELIVERY = ("simulate_delivery_stream", "delivery_status_stream")

    def __init__(self, listen_stream: str, send_stream: str) -> None:
        self.listen_stream = listen_stream
        self.send_stream = send_stream


class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"


class DeliveryStatus(str, Enum):
    WAITING_FOR_PICKUP = "waiting_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
