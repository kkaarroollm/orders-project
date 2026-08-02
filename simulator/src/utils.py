import logging
from typing import Any

from shared.redis.publisher import StreamProducer
from shared.redis.scheduler import RedisScheduler

from src.schemas import SimulationStream
from src.strategies import SIMULATION_STEPS


def _timer(stream: SimulationStream, entity_id: str, step: int) -> dict[str, Any]:
    return {"kind": stream.name, "entity_id": entity_id, "step": step}


async def start_simulation(
    stream: SimulationStream,
    entity_id: str,
    scheduler: RedisScheduler,
) -> None:
    steps = SIMULATION_STEPS[stream]
    logging.info("Starting %s simulation for %s", stream.name, entity_id)
    await scheduler.schedule(_timer(stream, entity_id, 0), delay_seconds=steps[0].delay_seconds)


async def run_step(
    payload: dict[str, Any],
    scheduler: RedisScheduler,
    producer: StreamProducer[Any],
) -> None:
    """Publish one status transition and schedule the next.

    Nothing is held in memory between steps, so a restart mid-simulation
    resumes from whatever timer is still pending in Redis.
    """
    stream = SimulationStream[payload["kind"]]
    steps = SIMULATION_STEPS[stream]
    index = payload["step"]
    entity_id = payload["entity_id"]

    step = steps[index]
    await producer.publish(step.event(id=entity_id, status=step.status), correlation_id=entity_id)
    logging.info("%s %s -> %s", stream.name, entity_id, step.status)

    if index + 1 < len(steps):
        await scheduler.schedule(
            _timer(stream, entity_id, index + 1),
            delay_seconds=steps[index + 1].delay_seconds,
        )
