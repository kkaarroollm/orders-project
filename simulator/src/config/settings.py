from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"

    simulate_order_stream: str = "simulate-order-stream"
    simulate_delivery_stream: str = "simulate-delivery-stream"
    order_status_stream: str = "order-status-stream"
    delivery_status_stream: str = "delivery-status-stream"

    simulator_group: str = "simulator-group"

    order_confirming_delay: int = 20
    order_preparing_delay: int = 200
    delivery_waiting_delay: int = 40
    delivery_way_delay: int = 20

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
