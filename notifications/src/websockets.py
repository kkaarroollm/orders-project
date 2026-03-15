import logging
from typing import Any

from fastapi import WebSocket


class OrderStatusConnectionManager:
    def __init__(self) -> None:
        self._active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, order_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if order_id not in self._active_connections:
            self._active_connections[order_id] = []
        self._active_connections[order_id].append(websocket)
        logging.info("User connected for order %s", order_id)

    def disconnect(self, order_id: str, websocket: WebSocket) -> None:
        if order_id in self._active_connections:
            self._active_connections[order_id].remove(websocket)
            if not self._active_connections[order_id]:
                del self._active_connections[order_id]
        logging.info("User disconnected from order %s", order_id)

    async def broadcast(self, order_id: str, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for conn in self._active_connections.get(order_id, []):
            try:
                await conn.send_json(message)
            except Exception:
                logging.warning("Dead connection detected for order %s, removing", order_id)
                dead.append(conn)
        for conn in dead:
            self.disconnect(order_id, conn)
        logging.info("Broadcast message to order %s: %s", order_id, message)


ws_order_status_manager: OrderStatusConnectionManager = OrderStatusConnectionManager()
