import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.lifespan import startup, teardown
from src.routes import router, health_router
from src.websockets import ws_order_status_manager


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator:
    """Handles application startup and shutdown."""
    await startup(app_)
    yield
    await teardown(app_)


app = FastAPI(
    title="Notifications Service",
    version="1.0.0",
    contact={"name": "kkaarroollm", "email": "mkarol.4514@gmail.com"},  # noqa
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.websocket("/order-tracking/{order_id}/ws")
async def websocket_order_tracking(websocket: WebSocket, order_id: str):
    await ws_order_status_manager.connect(order_id, websocket)
    noti_repo = app.state.notification_repo

    if status := await noti_repo.get_order_status(order_id):
        try:
            await websocket.send_json(status)
        except WebSocketDisconnect:
            logging.warning(f"⚠️ Client disconnected before receiving initial status: {order_id}")
            ws_order_status_manager.disconnect(order_id, websocket)
            return

    try:
        while True:
            await websocket.receive_text()  # Keep connection open
    except WebSocketDisconnect:
        logging.info(f"❌ WebSocket disconnected for order {order_id}")
        ws_order_status_manager.disconnect(order_id, websocket)



    # await ws_order_status_manager.connect(order_id, websocket)
    #
    # try:
    #     while True:
    #         await websocket.receive_text()
    # except WebSocketDisconnect:
    #     ws_order_status_manager.disconnect(order_id, websocket)
app.include_router(health_router)
