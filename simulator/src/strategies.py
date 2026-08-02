import asyncio
import logging
from typing import Any

from shared.events.delivery import DeliveryStatusSimulated
from shared.events.order import OrderStatusSimulated
from shared.redis.publisher import StreamProducer

from src.schemas import DeliveryStatus, OrderStatus, SimulationStream
from src.settings import settings


class OrderSimulationStrategy:
    async def process(self, entity_id: str, producer: StreamProducer[Any]) -> None:
        logging.info("Starting ORDER simulation for %s", entity_id)

        for delay, status in (
            (settings.order_confirming_delay, OrderStatus.PREPARING),
            (settings.order_preparing_delay, OrderStatus.OUT_FOR_DELIVERY),
        ):
            await asyncio.sleep(delay)
            await producer.publish(
                OrderStatusSimulated(id=entity_id, status=status.value),
                correlation_id=entity_id,
            )
            logging.info("Order %s -> %s", entity_id, status)


class DeliverySimulationStrategy:
    async def process(self, entity_id: str, producer: StreamProducer[Any]) -> None:
        logging.info("Starting DELIVERY simulation for %s", entity_id)

        for delay, status in (
            (settings.delivery_waiting_delay, DeliveryStatus.ON_THE_WAY),
            (settings.delivery_way_delay, DeliveryStatus.DELIVERED),
        ):
            await asyncio.sleep(delay)
            await producer.publish(
                DeliveryStatusSimulated(id=entity_id, status=status.value),
                correlation_id=entity_id,
            )
            logging.info("Delivery %s -> %s", entity_id, status)


SIMULATION_STRATEGY: dict[SimulationStream, OrderSimulationStrategy | DeliverySimulationStrategy] = {
    SimulationStream.ORDER: OrderSimulationStrategy(),
    SimulationStream.DELIVERY: DeliverySimulationStrategy(),
}
