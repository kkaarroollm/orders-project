from fastapi import FastAPI

from src.services.delivery_service import DeliveryService
from src.streams import RedisStreamPublisher


async def setup_services(app: FastAPI) -> None:
    """Initialize all services with required dependencies and attach to app state."""
    repo = app.state.delivery_repo
    publisher = RedisStreamPublisher(app.state.redis_client)

    app.state.delivery_service = DeliveryService(repo=repo, publisher=publisher)


__all__ = [
    "DeliveryService",
    "setup_services",
]
