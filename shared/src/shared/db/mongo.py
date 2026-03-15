import logging
from types import TracebackType

from pymongo import AsyncMongoClient
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase


async def connect_mongo(url: str, database: str) -> tuple[AsyncMongoClient, AsyncDatabase]:
    mongo_client: AsyncMongoClient = AsyncMongoClient(url)
    db = mongo_client[database]

    try:
        await db.command("ping")
        logging.info("MongoDB connection established.")
    except Exception as e:
        raise ConnectionError(f"MongoDB ping error: {e}") from e

    return mongo_client, db


class MongoTransactionManager:
    def __init__(self, client: AsyncMongoClient) -> None:
        self._client = client
        self._session: AsyncClientSession | None = None

    async def __aenter__(self) -> AsyncClientSession:
        self._session = await self._client.start_session()
        self._session.start_transaction()
        return self._session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        assert self._session is not None
        if exc_type:
            await self._session.abort_transaction()
        else:
            await self._session.commit_transaction()
        await self._session.end_session()
