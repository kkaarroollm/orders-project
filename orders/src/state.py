from dataclasses import dataclass, field

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis
from shared.redis.event_bus import EventBus

from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository
from src.services.menu_service import MenuService
from src.services.order_service import OrderService


@dataclass
class AppState:
    mongo_client: AsyncMongoClient
    database: AsyncDatabase
    redis_client: Redis
    menu_repository: MenuItemRepository
    order_repository: OrderRepository
    menu_service: MenuService
    order_service: OrderService
    event_bus: EventBus | None = field(default=None)
    ready: bool = field(default=False)
