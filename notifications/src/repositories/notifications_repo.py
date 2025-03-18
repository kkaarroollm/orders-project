import json
import logging

from redis.asyncio import Redis

logging.basicConfig(level=logging.INFO)


class NotificationRepository:
    def __init__(self, redis_client: Redis):
        self._redis = redis_client

    async def send_notification(self, message: dict) -> None:
        print(f"Notification sent: {message}")
        # TODO: Implement socket for frontend notifications

    async def subscribe_to_events(self, *channels: str) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(*channels)

        async for message in pubsub.listen():
            print(f"📡 Received message for notification: {message}")
            if message["type"] == "message":
                print(f"📦 Processing event: {message}")
                logging.info(f"📦 Processing event: {message}")
                event_data = json.loads(message["data"])
                await self.send_notification(event_data)
