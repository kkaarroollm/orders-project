from typing import Optional

from pydantic import BaseModel

from src.schemas import OrderSchema


class OrderResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    order: Optional[OrderSchema] = None
