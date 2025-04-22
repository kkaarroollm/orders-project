import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.config import settings
from src.lifespan import startup, teardown
from src.routes import router
from src.websockets import ws_order_status_manager


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator:
    """Handles application startup and shutdown."""
    await startup(app_)
    yield
    await teardown(app_)


app: FastAPI = FastAPI(
    title=settings.title,
    version=settings.version,
    contact={
        "name": settings.contact_name,
        "email": settings.contact_email,
    },
    openapi_url=None if not settings.environment.docs_available() else "/openapi.json",
    lifespan=lifespan,
)


@app.websocket("/ws/v1/order-tracking/{order_id}")
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


app.include_router(router)

app.add_middleware(GZipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
