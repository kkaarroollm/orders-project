from dataclasses import dataclass, field

from redis.asyncio import Redis
from shared.redis.event_bus import EventBus

from src.repository import NotificationRepository
from src.service import NotificationService, StatusPushFanout


@dataclass
class AppState:
    redis_client: Redis
    notification_repository: NotificationRepository
    notification_service: NotificationService
    status_push_fanout: StatusPushFanout
    event_bus: EventBus | None = field(default=None)
    fanout_bus: EventBus | None = field(default=None)
    ready: bool = field(default=False)
