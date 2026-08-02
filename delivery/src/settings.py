from shared.settings import BaseServiceSettings

__all__ = ["settings"]


class Settings(BaseServiceSettings):
    title: str = "Delivery Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa: N815
    contact_email: str = "mkarol.4514@gmail.com"

    mongo_collection_deliveries: str = "deliveries"

    # Stream names live on the event classes in `shared.events`.
    delivery_group: str = "delivery-group"


settings = Settings()
