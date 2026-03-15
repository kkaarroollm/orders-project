from typing import Any, Protocol, runtime_checkable

from fastapi import WebSocket


@runtime_checkable
class OrderStatusConnectionManagerProtocol(Protocol):
    async def connect(self, order_id: str, websocket: WebSocket) -> None: ...
    def disconnect(self, order_id: str, websocket: WebSocket) -> None: ...
    async def broadcast(self, order_id: str, message: dict[str, Any]) -> None: ...
