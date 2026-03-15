from pydantic import BaseModel

from src.schemas import OrderSchema


class OrderResponse(BaseModel):
    success: bool
    message: str | None = None
    order: OrderSchema | None = None
