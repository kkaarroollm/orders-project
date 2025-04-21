from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = f"redis://localhost:6379"

    simulate_order_stream: str = "simulate-order-stream"
    simulate_delivery_stream: str = "simulate-delivery-stream"
    order_status_stream: str = "order-status-stream"
    delivery_status_stream: str = "delivery-status-stream"

    simulator_group: str = "simulator-group"

    order_confirming_delay: int = 20
    order_preparing_delay: int = 200
    delivery_waiting_delay: int = 40
    delivery_way_delay: int = 20

    model_config = SettingsConfigDict(env_file=".env")

    @model_validator(mode="after")
    def setup_dynamic_settings(self):
        self.redis_url = f"redis://{self.redis_host}:{self.redis_port}"
        return self


settings = Settings()
