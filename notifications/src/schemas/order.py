from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, BeforeValidator, Field

StrObjectId = Annotated[str, BeforeValidator(str)]


class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"


class OrderedItemSchema(BaseModel):
    item_id: StrObjectId
    quantity: int


class OrderingPersonSchema(BaseModel):
    first_name: str
    last_name: str
    address: str
    phone_number: str


class OrderSchema(BaseModel):
    id: Optional[StrObjectId] = Field(alias="_id")
    person: OrderingPersonSchema
    items: List[OrderedItemSchema]
    total_price: float
    status: OrderStatus
    simulation: int
    created_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True
