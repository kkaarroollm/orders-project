from typing import Protocol, runtime_checkable


@runtime_checkable
class DeliveryServiceProtocol(Protocol):
    async def handle_order(self, order_data: dict) -> None: ...  # type: ignore[type-arg]
    async def handle_status_update(self, status_data: dict) -> None: ...  # type: ignore[type-arg]
