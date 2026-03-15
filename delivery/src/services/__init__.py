from typing import Any

from fastapi import FastAPI
from shared.redis.publisher import StreamProducer

from src.services.delivery_service import DeliveryService


async def setup_services(app: FastAPI) -> None:
    repo = app.state.delivery_repo
    publisher: StreamProducer[Any] = StreamProducer(app.state.redis_client)
    app.state.delivery_service = DeliveryService(repo=repo, publisher=publisher)


__all__ = ["DeliveryService", "setup_services"]
