from enum import Enum
from typing import Annotated

from pydantic import BeforeValidator

StrObjectId = Annotated[str, BeforeValidator(str)]


class DeliveryStatus(str, Enum):
    WAITING_FOR_PICKUP = "waiting_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"

