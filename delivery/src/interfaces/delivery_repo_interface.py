from typing import Protocol, runtime_checkable

from pymongo.asynchronous.client_session import AsyncClientSession

from src.schemas import DeliverySchema, DeliveryStatus


@runtime_checkable
class DeliveryRepositoryProtocol(Protocol):
    async def create(self, data: DeliverySchema, session: AsyncClientSession | None = None) -> str: ...
    async def get_by_id(self, id: str, session: AsyncClientSession | None = None) -> DeliverySchema | None: ...
    async def find_one(self, filter: dict, session: AsyncClientSession | None = None) -> DeliverySchema | None: ...  # type: ignore[type-arg]
    async def update_status(self, delivery_id: str, new_status: DeliveryStatus) -> bool: ...
