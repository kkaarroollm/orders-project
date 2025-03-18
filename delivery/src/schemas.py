from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

StrObjectId = Annotated[str, BeforeValidator(str)]


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"


class CourierSchema(BaseModel):
    first_name: str
    last_name: str
    phone_number: str


class DeliverySchema(BaseModel):
    id: Optional[StrObjectId] = Field(alias="_id", default=None)
    order_id: StrObjectId
    status: DeliveryStatus
    courier: CourierSchema

    class Config:
        populate_by_name = True
        from_attributes = True
