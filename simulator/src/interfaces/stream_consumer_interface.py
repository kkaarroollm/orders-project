from abc import ABC, abstractmethod
from typing import Awaitable, Callable


class IRedisStreamConsumer(ABC):
    """Interface for Redis Stream Consumer"""

    @abstractmethod
    async def bind_group(self) -> None:
        """Bind a consumer group to the stream."""
        ...

    @abstractmethod
    async def listen(self, handler: Callable[[dict], Awaitable[None]]) -> None:
        """Continuously listen for new messages and call the handler on each one."""
        ...
