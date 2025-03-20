import logging
from fastapi import WebSocket


class OrderStatusConnectionManager:
    def __init__(self):
        self._active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, order_id: str, websocket: WebSocket):
        await websocket.accept()

        if order_id not in self._active_connections:
            self._active_connections[order_id] = []
        self._active_connections[order_id].append(websocket)
        logging.info(f"User connected for order {order_id}")

    def disconnect(self, order_id: str, websocket: WebSocket):
        if order_id in self._active_connections:
            self._active_connections[order_id].remove(websocket)
            if not self._active_connections[order_id]:
                del self._active_connections[order_id]
        logging.info(f"User disconnected from order {order_id}")

    async def broadcast(self, order_id: str, message: dict) -> None:
        if order_id in self._active_connections:
            for connection in self._active_connections[order_id]:
                await connection.send_json(message)
        logging.info(f"Broadcast message to order {order_id}: {message}")


ws_order_status_manager = OrderStatusConnectionManager()
