from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

StrObjectId = Annotated[str, BeforeValidator(str)]


class BaseDocument(BaseModel):
    id: StrObjectId | None = Field(alias="_id", default=None)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
