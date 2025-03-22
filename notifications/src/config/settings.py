from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    title: str = "Notification Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa
    contact_email: str = "mkarol.4514@gmail.com"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = f"redis://{redis_host}:{redis_port}"

    orders_stream: str = "orders-stream"
    deliveries_stream: str = "deliveries-stream"

    notifications_group: str = "notifications-group"

    class Config:
        env_file = ".env"


settings = Settings()
