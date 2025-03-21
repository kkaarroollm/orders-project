import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Optional

from redis.asyncio import Redis

from src.schemas import SimulationStream
from src.strategies import SIMULATION_STRATEGY


async def get_last_processed_ids(redis_client: Redis) -> dict[str, str]:
    return {
        stream.listen_stream: (await redis_client.get(f"last_id:{stream.listen_stream}") or "0")
        for stream in SimulationStream
    }


async def store_last_processed_id(redis_client: Redis, stream_name: str, last_id: str) -> None:
    await redis_client.set(f"last_id:{stream_name}", last_id)


async def read_redis_stream(redis_client: Redis, block: int, count: int) -> Any:
    last_ids: dict[str, str] = await get_last_processed_ids(redis_client)

    try:
        stream_data = await redis_client.xread(last_ids, block=block, count=count)  # type: ignore
        if stream_data:
            for stream_name, messages in stream_data:
                await store_last_processed_id(redis_client, stream_name, messages[-1][0])
        return stream_data
    except Exception as e:
        logging.error(f"Error reading Redis stream: {e}")
        return None


async def parse_stream_messages(messages: list[dict], stream: str) -> AsyncGenerator:
    for message_id, message_data in messages:
        try:
            event_data: dict[str, Any] = json.loads(message_data.get("data"))
            yield stream, message_id, event_data
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding message data: {e}")


async def fetch_stream_events(redis_client: Redis, block: int = 5000, count: int = 1) -> AsyncGenerator:
    while True:
        stream_data = await read_redis_stream(redis_client, block, count)
        if not stream_data:
            await asyncio.sleep(1)
            continue

        for stream, messages in stream_data:
            async for parsed_event in parse_stream_messages(messages, stream):
                yield parsed_event


async def handle_event(
    entity_id: str,
    redis_client: Redis,
    simulation_stream: SimulationStream,
) -> None:
    async with asyncio.Semaphore(10):
        strategy = SIMULATION_STRATEGY.get(simulation_stream)
        if not strategy:
            logging.warning(f"No simulation strategy found for {simulation_stream}")
            return

        await strategy.process(entity_id, redis_client, simulation_stream.send_stream)


async def start_stream_worker(redis_client: Redis) -> None:
    input_streams: dict[str, SimulationStream] = {stream.listen_stream: stream for stream in SimulationStream}

    async for stream, message_id, event_data in fetch_stream_events(redis_client):
        entity_id: Optional[str] = event_data.get("id")
        simulation_stream: Optional[SimulationStream] = input_streams.get(stream)

        if not entity_id or not simulation_stream:
            logging.warning(f"Invalid event data: {event_data}")
            continue

        asyncio.create_task(handle_event(entity_id, redis_client, simulation_stream))
