import asyncio
import logging
from typing import Any

from shared.redis.publisher import StreamProducer

from src.schemas import DeliveryStatus, OrderStatus, SimulationStream
from src.settings import settings


class OrderSimulationStrategy:
    async def process(self, entity_id: str, producer: StreamProducer[Any], output_stream: str) -> None:
        logging.info("Starting ORDER simulation for %s", entity_id)
        await asyncio.sleep(settings.order_confirming_delay)
        await producer.publish_raw(output_stream, {"id": entity_id, "status": OrderStatus.PREPARING})
        logging.info("Order %s -> %s", entity_id, OrderStatus.PREPARING)

        await asyncio.sleep(settings.order_preparing_delay)
        await producer.publish_raw(output_stream, {"id": entity_id, "status": OrderStatus.OUT_FOR_DELIVERY})
        logging.info("Order %s -> %s", entity_id, OrderStatus.OUT_FOR_DELIVERY)


class DeliverySimulationStrategy:
    async def process(self, entity_id: str, producer: StreamProducer[Any], output_stream: str) -> None:
        logging.info("Starting DELIVERY simulation for %s", entity_id)
        await asyncio.sleep(settings.delivery_waiting_delay)
        await producer.publish_raw(output_stream, {"id": entity_id, "status": DeliveryStatus.ON_THE_WAY})
        logging.info("Delivery %s -> %s", entity_id, DeliveryStatus.ON_THE_WAY)

        await asyncio.sleep(settings.delivery_way_delay)
        await producer.publish_raw(output_stream, {"id": entity_id, "status": DeliveryStatus.DELIVERED})
        logging.info("Delivery %s -> %s", entity_id, DeliveryStatus.DELIVERED)


SIMULATION_STRATEGY: dict[SimulationStream, OrderSimulationStrategy | DeliverySimulationStrategy] = {
    SimulationStream.ORDER: OrderSimulationStrategy(),
    SimulationStream.DELIVERY: DeliverySimulationStrategy(),
}
