from pydantic import BaseModel
from pydantic.fields import Field
from datetime import datetime


class CacheSchema(BaseModel):
    order_id: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
