from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies import get_order_service
from src.responses import OrderResponse
from src.schemas import OrderSchema
from src.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderSchema,
    order_service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    response = await order_service.create_order_with_stock_check(order_data)
    if not response.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
    return response


@router.get("/{order_id}", response_model=OrderSchema, status_code=status.HTTP_200_OK)
async def get_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
) -> OrderSchema:
    if not (order := await order_service.get(order_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
