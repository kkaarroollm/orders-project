from shared.settings import BaseServiceSettings, EnvironmentEnum

__all__ = ["EnvironmentEnum", "settings"]


class Settings(BaseServiceSettings):
    title: str = "Orders Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa: N815
    contact_email: str = "mkarol.4514@gmail.com"

    mongo_collection_orders: str = "orders"
    mongo_collection_menu_items: str = "menu_items"

    orders_stream: str = "orders-stream"
    orders_group: str = "orders-group"

    simulate_order_stream: str = "simulate-order-stream"
    order_status_stream: str = "order-status-stream"


settings = Settings()
