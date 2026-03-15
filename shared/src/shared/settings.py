from enum import Enum

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentEnum(str, Enum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"

    def docs_available(self) -> bool:
        return self in {EnvironmentEnum.DEVELOPMENT}


class BaseServiceSettings(BaseSettings):
    environment: EnvironmentEnum = EnvironmentEnum.DEVELOPMENT
    debug: bool = False

    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "food-delivery"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = ""

    cors_allow_credentials: bool = False
    cors_allow_origins: list[str] = []
    cors_allow_methods: list[str] = []
    cors_allow_headers: list[str] = []

    model_config = SettingsConfigDict(env_file=".env")

    @model_validator(mode="after")
    def setup_dynamic_settings(self) -> "BaseServiceSettings":
        if self.debug:
            self.cors_allow_origins = ["*"]
            self.cors_allow_methods = ["*"]
            self.cors_allow_headers = ["*"]
        if not self.redis_url:
            self.redis_url = f"redis://{self.redis_host}:{self.redis_port}"
        return self
