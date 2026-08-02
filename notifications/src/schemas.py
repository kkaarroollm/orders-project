from datetime import UTC, datetime

from pydantic import BaseModel, Field


class CacheSchema(BaseModel):
    order_id: str
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
