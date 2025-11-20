from fastapi import APIRouter
from backend.app.permissions import set_acl_record, list_acls, delete_acl_record

router = APIRouter()

@router.get("/list")
def get_acls():
    return {"acls": list_acls()}

@router.post("/set")
def create_acl(path: str, username: str, permissions: str):
    return set_acl_record(path, username, permissions)

@router.delete("/delete")
def remove_acl(path: str, username: str):
    return delete_acl_record(path, username)
