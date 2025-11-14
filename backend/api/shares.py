# backend/api/shares.py
from fastapi import APIRouter, Body, HTTPException
from backend.storage.share_manager import list_shares, add_share, remove_share, update_share

router = APIRouter()

@router.post("/listshares")
def post_list_shares():
    return {"response": list_shares(), "error": None}

@router.post("/add")
def post_add_share(payload: dict = Body(...)):
    name = payload.get("name")
    path = payload.get("path")
    protocol = payload.get("protocol", "smb")
    if not name or not path:
        raise HTTPException(status_code=400, detail="name and path required")
    return {"response": add_share(name, path, protocol), "error": None}

@router.post("/remove")
def post_remove_share(payload: dict = Body(...)):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    return {"response": remove_share(name), "error": None}
