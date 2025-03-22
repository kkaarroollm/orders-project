import asyncio
import json
import logging

from redis.asyncio import Redis

from src.config import settings
from src.interfaces import ISimulationStrategy
from src.schemas import DeliveryStatus, OrderStatus, SimulationStream


class OrderSimulationStrategy(ISimulationStrategy):
    async def process(self, entity_id: str, redis_client: Redis, output_stream: str) -> None:
        logging.info(f"Starting ORDER simulation for {entity_id}")
        await asyncio.sleep(settings.order_confirming_delay)
        await redis_client.xadd(output_stream, {"data": json.dumps({"id": entity_id, "status": OrderStatus.PREPARING})})
        logging.info(f"Order {entity_id} -> {OrderStatus.PREPARING}")

        await asyncio.sleep(settings.order_preparing_delay)
        await redis_client.xadd(
            output_stream, {"data": json.dumps({"id": entity_id, "status": OrderStatus.OUT_FOR_DELIVERY})}
        )
        logging.info(f"Order {entity_id} -> {OrderStatus.OUT_FOR_DELIVERY}")


class DeliverySimulationStrategy(ISimulationStrategy):
    async def process(self, entity_id: str, redis_client: Redis, output_stream: str) -> None:
        logging.info(f"Starting DELIVERY simulation for {entity_id}")
        await asyncio.sleep(settings.delivery_waiting_delay)
        await redis_client.xadd(
            output_stream, {"data": json.dumps({"id": entity_id, "status": DeliveryStatus.ON_THE_WAY})}
        )
        logging.info(f"Delivery {entity_id} -> {DeliveryStatus.ON_THE_WAY}")

        await asyncio.sleep(settings.delivery_way_delay)
        await redis_client.xadd(
            output_stream, {"data": json.dumps({"id": entity_id, "status": DeliveryStatus.DELIVERED})}
        )
        logging.info(f"Delivery {entity_id} -> {DeliveryStatus.DELIVERED}")


SIMULATION_STRATEGY = {
    SimulationStream.ORDER: OrderSimulationStrategy(),
    SimulationStream.DELIVERY: DeliverySimulationStrategy(),
}
