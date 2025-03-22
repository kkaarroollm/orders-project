from fastapi import FastAPI

from src.services.notification_service import NotificationService
from src.websockets import ws_order_status_manager


async def setup_services(app: FastAPI) -> None:
    app.state.notification_service = NotificationService(app.state.notification_repository, ws_order_status_manager)
