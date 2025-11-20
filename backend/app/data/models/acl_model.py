from pydantic import BaseModel

class ACLModel(BaseModel):
    path: str
    user: str
    permissions: str  # rwx, rw-, r--
