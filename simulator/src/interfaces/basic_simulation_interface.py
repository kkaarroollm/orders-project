from typing import Protocol, runtime_checkable

from shared.redis.publisher import StreamProducer


@runtime_checkable
class SimulationStrategyProtocol(Protocol):
    async def process(self, entity_id: str, producer: StreamProducer, output_stream: str) -> None: ...  # type: ignore[type-arg]
