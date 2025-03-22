from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    title: str = "Delivery Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa
    contact_email: str = "mkarol.4514@gmail.com"

    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "food-delivery"
    mongo_collection_deliveries: str = "deliveries"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = f"redis://{redis_host}:{redis_port}"

    orders_stream: str = "orders-stream"
    deliveries_stream: str = "deliveries-stream"
    simulate_delivery_stream: str = "simulate-delivery-stream"
    delivery_status_stream: str = "delivery-status-stream"
    delivery_group: str = "delivery-group"

    class Config:
        env_file = ".env"


settings = Settings()
