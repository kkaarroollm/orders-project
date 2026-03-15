from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NotificationRepositoryProtocol(Protocol):
    async def set_order_status(self, order_id: str, message: dict[str, Any], expire: int = 86400) -> None: ...
    async def get_order_status(self, order_id: str) -> dict[str, Any]: ...
