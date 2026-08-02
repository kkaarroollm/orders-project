from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, field_serializer
from shared.schemas.base import BaseDocument, StrObjectId


class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"


# Which statuses an order may move *from* to reach a given status. Streams
# guarantee order within one stream, not across retries and redeliveries, so a
# late `preparing` must not drag an order back from `out_for_delivery`.
ALLOWED_PREVIOUS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PREPARING: {OrderStatus.CONFIRMED},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.PREPARING},
}


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
    version: int = Field(default=0)
    # Client-supplied, so it is bounded: -1 disables simulation, 1 enables it.
    simulation: int = Field(default=1, ge=-1, le=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_serializer("total_price", when_used="json")
    def serialize_total_price(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None
