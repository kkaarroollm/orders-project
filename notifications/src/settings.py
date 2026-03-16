from shared.settings import BaseServiceSettings

__all__ = ["settings"]


class Settings(BaseServiceSettings):
    title: str = "Notification Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa: N815
    contact_email: str = "mkarol.4514@gmail.com"

    orders_stream: str = "orders-stream"
    deliveries_stream: str = "deliveries-stream"
    notifications_group: str = "notifications-group"


settings = Settings()
