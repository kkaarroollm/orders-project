from abc import ABC, abstractmethod

from redis.asyncio import Redis


class ISimulationStrategy(ABC):
    @abstractmethod
    async def process(self, entity_id: str, redis_client: Redis, output_stream: str) -> None: ...
