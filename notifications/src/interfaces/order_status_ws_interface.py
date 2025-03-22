from abc import ABC, abstractmethod

from fastapi import WebSocket


class IOrderStatusConnectionManager(ABC):
    @abstractmethod
    async def connect(self, order_id: str, websocket: WebSocket) -> None: ...

    @abstractmethod
    def disconnect(self, order_id: str, websocket: WebSocket) -> None: ...

    @abstractmethod
    async def broadcast(self, order_id: str, message: dict) -> None: ...
