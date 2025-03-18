from pydantic import BaseModel

from src.schemas import OrderSchema


class OrderResponse(BaseModel):
    order: OrderSchema
    message: str = "Order created successfully"
    success: bool = True
