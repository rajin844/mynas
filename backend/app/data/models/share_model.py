from pydantic import BaseModel, Field

class ShareModel(BaseModel):
    name: str
    path: str
    protocol: str = "smb"  # or nfs
