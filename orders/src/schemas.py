from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, field_serializer
from shared.schemas.base import BaseDocument, StrObjectId


class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"


class MenuItemSchema(BaseDocument):
    name: str
    description: str | None = None
    price: float
    category: str
    stock: int


class OrderedItemSchema(BaseDocument):
    item_id: StrObjectId
    quantity: int


class OrderingPersonSchema(BaseDocument):
    first_name: str
    last_name: str
    address: str
    phone_number: str


class OrderSchema(BaseDocument):
    person: OrderingPersonSchema
    items: list[OrderedItemSchema]
    total_price: Decimal | None = Field(default=None)
    status: OrderStatus = OrderStatus.CONFIRMED
    simulation: int = 1
    created_at: datetime = Field(default_factory=datetime.now)

    @field_serializer("total_price", when_used="json")
    def serialize_total_price(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None
