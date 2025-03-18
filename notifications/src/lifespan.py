import asyncio
import logging

from fastapi import FastAPI
from redis.asyncio import Redis

from common.logging.setup import setup_logging
from src.database import connect_redis
from src.repositories import NotificationRepository


async def startup(app: FastAPI) -> None:
    """Startup sequence: Connect to Redis & initialize resources."""
    app.state.ready = False
    setup_logging()

    redis_client: Redis = await connect_redis()
    app.state.redis_client = redis_client

    app.state.notification_repo = NotificationRepository(redis_client=redis_client)
    app.state.subscription_task = asyncio.create_task(
        app.state.notification_repo.subscribe_to_events("orders_channel", "delivery_channel")
    )

    app.state.ready = True


async def teardown(app: FastAPI) -> None:
    """Teardown sequence: Cancel subscriptions & close Redis connection."""
    app.state.ready = False

    subscription_task = getattr(app.state, "subscription_task", None)
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
