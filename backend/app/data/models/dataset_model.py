from pydantic import BaseModel, Field

class DatasetModel(BaseModel):
    name: str = Field(min_length=1)
    pool: str = Field(min_length=1)
    mountpoint: str = Field(default="")
