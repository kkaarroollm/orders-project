from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from src.schemas.delivery import DeliveryStatus
from src.schemas.order import OrderSchema, OrderStatus


class EventType(str, Enum):
    ORDER_STATUS = "order_status"
    DELIVERY_STATUS = "delivery_status"
    NEW_ORDER = "new_order"
    SIMULATE_ORDER = "simulate_order"
    SIMULATE_DELIVERY = "simulate_delivery"


class StreamMessage(BaseModel):
    event: EventType
    new_status: OrderStatus | DeliveryStatus
    timestamp: Optional[datetime] = None
    order: OrderSchema
    delivery_id: Optional[str] = None
    extra: Optional[dict] = None
