from pymongo import AsyncMongoClient
from shared.db.mongo import MongoTransactionManager


class TransactionServiceMixin:
    def __init__(self, mongo_client: AsyncMongoClient) -> None:
        self._mongo_client = mongo_client

    def transaction(self) -> MongoTransactionManager:
        return MongoTransactionManager(self._mongo_client)
