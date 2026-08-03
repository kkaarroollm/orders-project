from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.dependencies import get_order_service
from src.responses import OrderResponse
from src.schemas import OrderSchema
from src.services.order_service import OrderService, RequestInProgressError

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderSchema,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="Retrying with the same key returns the original result instead of ordering twice.",
        ),
    ] = None,
    order_service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    try:
        response = await order_service.create_order_with_stock_check(order_data, idempotency_key)
    except RequestInProgressError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is still in progress",
        ) from None

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
