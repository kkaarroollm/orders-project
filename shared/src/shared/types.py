from typing import Any, Awaitable, Callable, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel
from pymongo.asynchronous.client_session import AsyncClientSession

T_co = TypeVar("T_co", bound=BaseModel, covariant=True)


@runtime_checkable
class ReadRepository(Protocol[T_co]):
    async def get_by_id(self, id: str, session: AsyncClientSession | None = None) -> T_co | None: ...
    async def find_one(
        self, filter: dict[str, Any], session: AsyncClientSession | None = None
    ) -> T_co | None: ...


@runtime_checkable
class WriteRepository(Protocol[T_co]):
    async def create(self, data: T_co, session: AsyncClientSession | None = None) -> str: ...  # type: ignore[misc]
    async def update_one(
        self, id: str, update: dict[str, Any], session: AsyncClientSession | None = None
    ) -> bool: ...


@runtime_checkable
class StreamPublisher(Protocol):
    async def publish_raw(self, stream: str, data: dict) -> None: ...  # type: ignore[type-arg]


@runtime_checkable
class StreamHandler(Protocol):
    async def __call__(self, data: dict) -> None: ...  # type: ignore[type-arg]


MessageHandler = Callable[[Any], Awaitable[None]]
