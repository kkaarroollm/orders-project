from dataclasses import dataclass, field

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis
from shared.redis.event_bus import EventBus

from src.repository import DeliveryRepository
from src.service import DeliveryService


@dataclass
class AppState:
    mongo_client: AsyncMongoClient
    database: AsyncDatabase
    redis_client: Redis
    delivery_repo: DeliveryRepository
    delivery_service: DeliveryService
    event_bus: EventBus | None = field(default=None)
    ready: bool = field(default=False)
