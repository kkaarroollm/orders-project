from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NotificationServiceProtocol(Protocol):
    async def handle_event(self, data: dict[str, Any]) -> None: ...
