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

    mongo_client, db = await connect_mongo(os.getenv("MONGO_URL", "default"))  # type: tuple[AsyncIOMotorClient, AsyncIOMotorDatabase]
    app.state.mongo_client = mongo_client
    app.state.db = db

    redis_client = await connect_redis()
    app.state.redis_client = redis_client

    app.state.delivery_repo = DeliveryRepository(collection=db.get_collection("deliveries"), redis_client=redis_client)

    app.state.subscription_task = asyncio.create_task(app.state.delivery_repo.subscribe_to_orders())
    app.state.ready = True
    logging.info("Delivery service is ready.")


async def teardown(app: FastAPI) -> None:
    """Teardown sequence: Close DB connections & cleanup resources."""
    app.state.ready = False
    subscription_task = getattr(app.state, "subscription_task")

    if subscription_task and not subscription_task.done():
        subscription_task.cancel()
        try:
            await asyncio.wait_for(subscription_task, timeout=5)
        except asyncio.TimeoutError:
            logging.error("Subscription task did not finish in time.")
        except asyncio.CancelledError:
            logging.error("Subscription task was successfully cancelled.")

    if redis_client := getattr(app.state, "redis_client"):
        await redis_client.close()

    if mongo_client := getattr(app.state, "mongo_client"):
        mongo_client.close()

    logging.info("Delivery service is shut down.")
