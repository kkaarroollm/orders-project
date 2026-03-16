from dataclasses import dataclass, field

from redis.asyncio import Redis
from shared.redis.event_bus import EventBus

from src.repository import NotificationRepository
from src.service import NotificationService


@dataclass
class AppState:
    redis_client: Redis
    notification_repository: NotificationRepository
    notification_service: NotificationService
    event_bus: EventBus | None = field(default=None)
    ready: bool = field(default=False)
