import asyncio
import logging
import os

from fastapi import FastAPI

from src.common import setup_logging
from src.database import connect_mongo, connect_redis
from src.repositories import DeliveryRepository


async def startup(app: FastAPI) -> None:
    """Startup sequence: Connect to DB & initialize resources."""
    app.state.ready = False
    setup_logging()

    mongo_client, db = await connect_mongo(os.getenv("MONGO_URL", "default"))
    app.state.mongo_client = mongo_client
    app.state.db = db

    redis_client = await connect_redis()
    app.state.redis_client = redis_client

    app.state.delivery_repo = DeliveryRepository(collection=db.get_collection("deliveries"), redis_client=redis_client)

    app.state.subscription_task = asyncio.create_task(app.state.delivery_repo.subscribe_to_orders())
    app.state.ready = True
    logging.info("Delivery service is ready.")


async def teardown(app: FastAPI) -> None:
    """Gracefully cancel tasks and close DB connections."""
    app.state.ready = False

    subscription_task = getattr(app.state, "subscription_task", None)
    if subscription_task and not subscription_task.done():
        subscription_task.cancel()
        try:
            await asyncio.wait_for(subscription_task, timeout=5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            logging.warning(f"Subscription task cancelled: {subscription_task.cancelled()}")

    delivery_repo = getattr(app.state, "delivery_repo", None)
    logging.error(delivery_repo.active_tasks)
    if delivery_repo and delivery_repo.active_tasks:
        res = await asyncio.gather(*delivery_repo.active_tasks, return_exceptions=True)
        logging.error(res)

    if redis_client := getattr(app.state, "redis_client", None):
        await redis_client.close()
    if mongo_client := getattr(app.state, "mongo_client", None):
        mongo_client.close()

    logging.info("Delivery service shut down.")
