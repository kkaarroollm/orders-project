from fastapi import FastAPI

from src.repositories.notifications_repo import NotificationRepository


async def setup_repository(app: FastAPI) -> None:
    app.state.notification_repository = NotificationRepository(app.state.redis_client)
