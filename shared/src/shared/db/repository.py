import logging
from typing import Any, Generic, TypeVar

from bson import ObjectId
from pydantic import BaseModel
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection

T = TypeVar("T", bound=BaseModel)


class MongoRepository(Generic[T]):
    def __init__(self, collection: AsyncCollection, model: type[T]) -> None:
        self._collection = collection
        self._model = model

    async def create(self, data: T, session: AsyncClientSession | None = None) -> str:
        doc = data.model_dump(by_alias=True, exclude={"id"}, mode="json")
        result = await self._collection.insert_one(doc, session=session)
        logging.debug("Inserted document %s into %s", result.inserted_id, self._collection.name)
        return str(result.inserted_id)

    async def get_by_id(self, id: str, session: AsyncClientSession | None = None) -> T | None:
        doc = await self._collection.find_one({"_id": ObjectId(id)}, session=session)
        return self._model(**doc) if doc else None

    async def find_one(
        self, filter: dict[str, Any], session: AsyncClientSession | None = None
    ) -> T | None:
        doc = await self._collection.find_one(filter, session=session)
        return self._model(**doc) if doc else None

    async def find_many(
        self,
        filter: dict[str, Any],
        session: AsyncClientSession | None = None,
        limit: int = 1000,
    ) -> list[T]:
        cursor = self._collection.find(filter, session=session)
        docs = await cursor.to_list(length=limit)
        return [self._model(**doc) for doc in docs]

    async def update_one(
        self,
        id: str,
        update: dict[str, Any],
        session: AsyncClientSession | None = None,
    ) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(id)},
            update,
            session=session,
        )
        return bool(result.modified_count)

    async def update_one_by_filter(
        self,
        filter: dict[str, Any],
        update: dict[str, Any],
        session: AsyncClientSession | None = None,
    ) -> bool:
        result = await self._collection.update_one(filter, update, session=session)
        return bool(result.modified_count)
