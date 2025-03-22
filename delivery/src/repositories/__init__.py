from fastapi import FastAPI

from src.config import settings
from src.repositories.delivery_repository import DeliveryRepository


async def setup_repositories(app: FastAPI) -> None:
    app.state.delivery_repo = DeliveryRepository(
        collection=app.state.database.get_collection(settings.mongo_collection_deliveries)
    )


__all__ = ["DeliveryRepository", "setup_repositories"]
