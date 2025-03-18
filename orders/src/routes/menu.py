from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_menu_repo
from src.repositories import MenuItemRepository
from src.schemas import MenuItemSchema

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("/items", response_model=list[MenuItemSchema])
async def get_all_menu_items(menu_repo: MenuItemRepository = Depends(get_menu_repo)) -> list[MenuItemSchema]:
    return await menu_repo.get_all_menu_items()


@router.post("/items", response_model=MenuItemSchema)
async def create_menu_item(
    item_data: MenuItemSchema, menu_repo: MenuItemRepository = Depends(get_menu_repo)
) -> MenuItemSchema | None:
    item_id = await menu_repo.create_menu_item(item_data)
    return await menu_repo.get_menu_item(item_id)


@router.get("/items/{item_id}", response_model=MenuItemSchema)
async def get_menu_item(item_id: str, menu_repo: MenuItemRepository = Depends(get_menu_repo)) -> MenuItemSchema:
    item = await menu_repo.get_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
