from motor.motor_asyncio import AsyncIOMotorClient

from src.databases import MongoDBTransactionManager


class TransactionServiceMixin:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self._mongo_client = mongo_client

    def transaction(self) -> MongoDBTransactionManager:
        return MongoDBTransactionManager(self._mongo_client)
