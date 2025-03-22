from types import TracebackType
from typing import Type

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession


class MongoDBTransactionManager:
    """Manages MongoDB transactions using async context management."""

    def __init__(self, client: AsyncIOMotorClient):
        self.client = client

    async def __aenter__(self) -> AsyncIOMotorClientSession:
        self.session = await self.client.start_session()
        self.transaction = self.session.start_transaction()
        return self.session

    async def __aexit__(
        self, exc_type: Type[BaseException], exc_value: BaseException, traceback: TracebackType
    ) -> None:
        if exc_type:
            await self.session.abort_transaction()
        else:
            await self.session.commit_transaction()
        await self.session.end_session()
