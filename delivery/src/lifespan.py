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
    subscription_tasks: set[asyncio.Task] = set()
    setup_logging()

    mongo_client, db = await connect_mongo(os.getenv("MONGO_URL", "default"))
    app.state.mongo_client = mongo_client
    app.state.db = db

    redis_client = await connect_redis()
    app.state.redis_client = redis_client

    app.state.delivery_repo = DeliveryRepository(collection=db.get_collection("deliveries"), redis_client=redis_client)

    subscription_tasks.add(asyncio.create_task(app.state.delivery_repo.subscribe_to_orders()))
    subscription_tasks.add(asyncio.create_task(app.state.delivery_repo.subscribe_to_status_changes()))
    app.state.subscription_tasks = subscription_tasks

    app.state.ready = True
    logging.info("Delivery service is ready.")


async def teardown(app: FastAPI) -> None:
    """Gracefully cancel tasks and close DB connections."""
    app.state.ready = False

    subscription_tasks = getattr(app.state, "subscription_tasks", [])
    for task in subscription_tasks:
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=5)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logging.warning(f"Subscription task cancelled: {task.cancelled()}")

    if redis_client := getattr(app.state, "redis_client", None):
        await redis_client.close()
    if mongo_client := getattr(app.state, "mongo_client", None):
        mongo_client.close()

    logging.info("Delivery service shut down.")
