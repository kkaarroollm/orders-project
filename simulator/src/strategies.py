import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod

from redis.asyncio import Redis

from src.schemas import DeliveryStatus, OrderStatus, SimulationStream


class BaseSimulationStrategy(ABC):
    @abstractmethod
    async def process(self, entity_id: str, redis_client: Redis, output_stream: str) -> None:
        raise NotImplementedError


class OrderSimulationStrategy(BaseSimulationStrategy):
    async def process(self, entity_id: str, redis_client: Redis, output_stream: str) -> None:
        logging.info(f"Starting ORDER simulation for {entity_id}")
        await asyncio.sleep(int(os.getenv("ORDER_CONFIRMING", "20")))
        await redis_client.xadd(output_stream, {"data": json.dumps({"id": entity_id, "status": OrderStatus.PREPARING})})
        logging.info(f"Order {entity_id} -> {OrderStatus.PREPARING}")

        await asyncio.sleep(int(os.getenv("ORDER_PREPARING", "200")))
        await redis_client.xadd(
            output_stream, {"data": json.dumps({"id": entity_id, "status": OrderStatus.OUT_FOR_DELIVERY})}
        )
        logging.info(f"Order {entity_id} -> {OrderStatus.OUT_FOR_DELIVERY}")


class DeliverySimulationStrategy(BaseSimulationStrategy):
    async def process(self, entity_id: str, redis_client: Redis, output_stream: str) -> None:
        logging.info(f"Starting DELIVERY simulation for {entity_id}")
        await asyncio.sleep(int(os.getenv("WAITING_FOR_PICKUP", "40")))
        await redis_client.xadd(
            output_stream, {"data": json.dumps({"id": entity_id, "status": DeliveryStatus.ON_THE_WAY})}
        )
        logging.info(f"Delivery {entity_id} -> {DeliveryStatus.ON_THE_WAY}")

        await asyncio.sleep(int(os.getenv("DELIVERY_WAY", "20")))
        await redis_client.xadd(
            output_stream, {"data": json.dumps({"id": entity_id, "status": DeliveryStatus.DELIVERED})}
        )
        logging.info(f"Delivery {entity_id} -> {DeliveryStatus.DELIVERED}")


SIMULATION_STRATEGY = {
    SimulationStream.ORDER: OrderSimulationStrategy(),
    SimulationStream.DELIVERY: DeliverySimulationStrategy(),
}
