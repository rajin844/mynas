from pydantic import BaseModel, Field

class UserModel(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=6)
    role: str = "user"
