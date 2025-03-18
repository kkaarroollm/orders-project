from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.repositories import MenuItemRepository, OrderRepository


def get_order_repo(request: Request) -> OrderRepository:
    db: AsyncIOMotorDatabase = request.app.state.db
    collection = db.get_collection("orders")
    return OrderRepository(
        collection=collection, mongo_client=request.app.state.mongo_client, redis_client=request.app.state.redis_client
    )


def get_menu_repo(request: Request) -> MenuItemRepository:
    db: AsyncIOMotorDatabase = request.app.state.db
    collection = db.get_collection("menu_items")
    return MenuItemRepository(collection=collection, redis_client=request.app.state.redis_client)
