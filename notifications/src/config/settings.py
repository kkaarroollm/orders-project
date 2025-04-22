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

    title: str = "Notification Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa
    contact_email: str = "mkarol.4514@gmail.com"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = ""

    orders_stream: str = "orders-stream"
    deliveries_stream: str = "deliveries-stream"

    notifications_group: str = "notifications-group"

    cors_allow_credentials: bool = False
    cors_allow_origins: list[str] = []
    cors_allow_methods: list[str] = []
    cors_allow_headers: list[str] = []

    @model_validator(mode="after")
    def setup_dynamic(self) -> "Settings":
        if self.debug:
            self.cors_allow_origins = ["*"]
            self.cors_allow_methods = ["*"]
            self.cors_allow_headers = ["*"]
        if not self.redis_url:
            self.redis_url = f"redis://{self.redis_host}:{self.redis_port}"
        return self

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
