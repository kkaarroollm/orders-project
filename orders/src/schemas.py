from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, BeforeValidator, Field

StrObjectId = Annotated[str, BeforeValidator(str)]


class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"

class MenuItemSchema(BaseModel):
    id: Optional[StrObjectId] = Field(alias="_id", default=None)
    name: str
    description: Optional[str] = None
    price: float
    category: str
    stock: int

    class Config:
        populate_by_name = True
        from_attributes = True


class OrderedItemSchema(BaseModel):
    item_id: StrObjectId
    quantity: int


class OrderingPersonSchema(BaseModel):
    first_name: str
    last_name: str
    address: str
    phone_number: str


class OrderSchema(BaseModel):
    id: Optional[StrObjectId] = Field(alias="_id", default=None)
    person: OrderingPersonSchema
    items: List[OrderedItemSchema]
    total_price: Optional[Decimal] = Field(alias="total_price", default=Decimal(0))
    status: OrderStatus = OrderStatus.CONFIRMED
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        from_attributes = True
