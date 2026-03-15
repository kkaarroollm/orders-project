from enum import Enum

from pydantic import BaseModel, Field
from shared.schemas.base import BaseDocument, StrObjectId


class DeliveryStatus(str, Enum):
    WAITING_FOR_PICKUP = "waiting_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"


class CourierSchema(BaseModel):
    first_name: str
    last_name: str
    phone_number: str


class DeliverySchema(BaseDocument):
    order_id: StrObjectId = Field(alias="order_id")
    status: DeliveryStatus = DeliveryStatus.WAITING_FOR_PICKUP
    courier: CourierSchema = Field(
        default_factory=lambda: CourierSchema(first_name="Random", last_name="Dude", phone_number="1234567890")
    )
