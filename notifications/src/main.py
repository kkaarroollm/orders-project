import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.lifespan import startup, teardown
from src.routes import health_router
from src.websockets import ws_order_status_manager


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator:
    """Handles application startup and shutdown."""
    await startup(app_)
    yield
    await teardown(app_)


app = FastAPI(
    title=settings.title,
    version=settings.version,
    contact={"name": settings.contact_name, "email": settings.contact_email},  # noqa
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/order-tracking/{order_id}/ws")
async def websocket_order_tracking(websocket: WebSocket, order_id: str) -> None:
    await ws_order_status_manager.connect(order_id, websocket)
    notifications_repo = app.state.notification_repository

    if status := await notifications_repo.get_order_status(order_id):
        try:
            await websocket.send_json(status)
        except WebSocketDisconnect:
            logging.warning(f"Client disconnected before receiving initial status: {order_id}")
            ws_order_status_manager.disconnect(order_id, websocket)
            return

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for order {order_id}")
        ws_order_status_manager.disconnect(order_id, websocket)


app.include_router(health_router)
