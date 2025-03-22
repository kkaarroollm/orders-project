from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_menu_service
from src.interfaces.menu_service_interface import IMenuService
from src.schemas import MenuItemSchema

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("/items", response_model=list[MenuItemSchema])
async def get_all_menu_items(
    menu_service: IMenuService = Depends(get_menu_service),
) -> list[MenuItemSchema]:
    return await menu_service.list_items()


@router.post("/items", response_model=MenuItemSchema)
async def create_menu_item(
    item_data: MenuItemSchema,
    menu_service: IMenuService = Depends(get_menu_service),
) -> MenuItemSchema:
    item_id = await menu_service.create_item(item_data)
    return item_data.model_copy(update={"id": item_id})


@router.get("/items/{item_id}", response_model=MenuItemSchema)
async def get_menu_item_by_id(
    item_id: str,
    menu_service: IMenuService = Depends(get_menu_service),
) -> MenuItemSchema:
    if not (item := await menu_service.get_item(item_id)):
        raise HTTPException(status_code=404, detail="Item not found")
    return item
