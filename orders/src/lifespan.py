import asyncio
import logging
import os

from fastapi import FastAPI
from redis.asyncio import Redis

from src.common import setup_logging
from src.database import connect_mongo, connect_redis
from src.repositories import OrderRepository


async def startup(app: FastAPI) -> None:
    """Startup sequence: Connect to DB & initialize resources."""
    app.state.ready = False
    setup_logging()

    mongo_client, db = await connect_mongo(os.getenv("MONGO_URL", "default"))
    app.state.mongo_client = mongo_client
    app.state.db = db

    redis_client: Redis = await connect_redis()
    app.state.redis_client = redis_client

    app.state.orders_repo = OrderRepository(
        collection=db.get_collection("orders"), mongo_client=mongo_client, redis_client=redis_client
    )
    app.state.subscription_tasks = asyncio.create_task(app.state.orders_repo.subscribe_to_status_changes())

    app.state.ready = True

    logging.info("Orders service is ready.")


async def teardown(app: FastAPI) -> None:
    """Teardown sequence: Close DB connections & cleanup resources."""
    app.state.ready = False

    if subscription_task := getattr(app.state, "subscription_task"):
        if not subscription_task.done():
            subscription_task.cancel()
            try:
                await asyncio.wait_for(subscription_task, timeout=5)
            except asyncio.TimeoutError:
                logging.warning(f"Subscription task cancelled: {subscription_task.cancelled()}")

    if redis_client := getattr(app.state, "redis_client"):
        await redis_client.close()

    if mongo_client := getattr(app.state, "mongo_client"):
        mongo_client.close()

    logging.info("Orders service is shut down.")
