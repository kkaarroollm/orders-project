from abc import ABC, abstractmethod


class IRedisStreamPublisher(ABC):
    @abstractmethod
    async def publish(self, stream: str, data: dict) -> None: ...
