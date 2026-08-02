from shared.settings import BaseServiceSettings, EnvironmentEnum

__all__ = ["EnvironmentEnum", "settings"]


class Settings(BaseServiceSettings):
    title: str = "Orders Service"
    version: str = "1.0.0"
    contact_name: str = "kkaarroollm"  # noqa: N815
    contact_email: str = "mkarol.4514@gmail.com"

    mongo_collection_orders: str = "orders"
    mongo_collection_menu_items: str = "menu_items"

    # Stream names live on the event classes in `shared.events`.
    orders_group: str = "orders-group"


settings = Settings()
