from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    title: str = "Orders Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa
    contact_email: str = "mkarol.4514@gmail.com"

    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "food-delivery"
    mongo_collection_orders: str = "orders"
    mongo_collection_menu_items: str = "menu_items"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = f"redis://{redis_host}:{redis_port}"

    orders_stream: str = "orders-stream"
    orders_group: str = "orders-group"

    simulate_order_stream: str = "simulate-order-stream"

    order_status_stream: str = "order-status-stream"

    class Config:
        env_file = ".env"


settings = Settings()
