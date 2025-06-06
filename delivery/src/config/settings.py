from enum import Enum

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentEnum(str, Enum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"

    def docs_available(self) -> bool:
        show_docs_environments = {EnvironmentEnum.DEVELOPMENT}
        return self in show_docs_environments


class Settings(BaseSettings):
    environment: EnvironmentEnum = EnvironmentEnum.DEVELOPMENT
    debug: bool = False

    title: str = "Delivery Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa
    contact_email: str = "mkarol.4514@gmail.com"

    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "food-delivery"
    mongo_collection_deliveries: str = "deliveries"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = ""

    orders_stream: str = "orders-stream"
    deliveries_stream: str = "deliveries-stream"
    simulate_delivery_stream: str = "simulate-delivery-stream"
    delivery_status_stream: str = "delivery-status-stream"
    delivery_group: str = "delivery-group"

    model_config = SettingsConfigDict(env_file=".env")

    @model_validator(mode="after")
    def setup_dynamic_settings(self) -> "Settings":
        if not self.redis_url:
            self.redis_url = f"redis://{self.redis_host}:{self.redis_port}"
        return self


settings = Settings()
