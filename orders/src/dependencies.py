from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.repositories import MenuItemRepository, OrderRepository


def get_order_repo(request: Request) -> OrderRepository:
    return request.app.state.orders_repo  # type: ignore


def get_menu_repo(request: Request) -> MenuItemRepository:
    db: AsyncIOMotorDatabase = request.app.state.db
    collection = db.get_collection("menu_items")
    return MenuItemRepository(collection=collection, redis_client=request.app.state.redis_client)
