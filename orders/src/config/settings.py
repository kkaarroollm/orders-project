from enum import Enum

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentEnum(str, Enum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"

    def docs_available(self):
        show_docs_environments = {EnvironmentEnum.DEVELOPMENT}
        return self in show_docs_environments


class Settings(BaseSettings):
    environment: EnvironmentEnum = EnvironmentEnum.DEVELOPMENT
    debug: bool = False

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
    redis_url: str = f"redis://localhost:6379"

    orders_stream: str = "orders-stream"
    orders_group: str = "orders-group"

    simulate_order_stream: str = "simulate-order-stream"

    order_status_stream: str = "order-status-stream"

    cors_allow_credentials: bool = False
    cors_allow_origins: list[str] = []
    cors_allow_methods: list[str] = []
    cors_allow_headers: list[str] = []
    allowed_hosts: list[str] = []

    @model_validator(mode="after")
    def setup_dynamic_settings(self):
        if self.debug:
            self.cors_allow_origins = ["*"]
            self.cors_allow_methods = ["*"]
            self.cors_allow_headers = ["*"]
            self.allowed_hosts = ["*"]
        self.redis_url = f"redis://{self.redis_host}:{self.redis_port}"
        return self

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
