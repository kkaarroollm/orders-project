from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_menu_repo, get_order_repo
from src.repositories import MenuItemRepository, OrderRepository
from src.responses import OrderResponse
from src.schemas import OrderSchema

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderSchema)
async def get_order(
    order_id: str, order_repo: OrderRepository = Depends(get_order_repo)
) -> OrderSchema | HTTPException:
    order = await order_repo.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderSchema,
    order_repo: OrderRepository = Depends(get_order_repo),
    menu_repo: MenuItemRepository = Depends(get_menu_repo),
) -> OrderResponse | HTTPException:
    result = await order_repo.create_order_with_stock_check(order_data, menu_repo)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result
