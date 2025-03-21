from datetime import datetime

from pydantic import BaseModel
from pydantic.fields import Field


class CacheSchema(BaseModel):
    order_id: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
