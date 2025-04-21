import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.config import EnvironmentEnum, settings
from src.lifespan import startup, teardown
from src.routes import router
from src.websockets import ws_order_status_manager

app_config = {
    "title": settings.title,
    "version": settings.version,
    "contact": {"name": settings.contact_name, "email": settings.contact_email},
}

if not settings.environment.docs_available():
    app_config["openapi_url"] = None


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator:
    """Handles application startup and shutdown."""
    await startup(app_)
    yield
    await teardown(app_)


app = FastAPI(**app_config, lifespan=lifespan)


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


app.include_router(router)


if settings.environment == EnvironmentEnum.PRODUCTION:
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)


app.add_middleware(GZipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
