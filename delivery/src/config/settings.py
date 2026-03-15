from shared.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    title: str = "Delivery Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa
    contact_email: str = "mkarol.4514@gmail.com"

    mongo_collection_deliveries: str = "deliveries"

    orders_stream: str = "orders-stream"
    deliveries_stream: str = "deliveries-stream"
    simulate_delivery_stream: str = "simulate-delivery-stream"
    delivery_status_stream: str = "delivery-status-stream"
    delivery_group: str = "delivery-group"


settings = Settings()
