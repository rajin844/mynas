# backend/api/shares.py
from fastapi import APIRouter, Body, HTTPException
from backend.storage.share_manager import list_shares, create_share, delete_share

router = APIRouter()

@router.post("/list")
def api_list():
    return {"response": list_shares(), "error": None}

@router.post("/create")
def api_create(payload: dict = Body(...)):
    if "name" not in payload or "path" not in payload:
        raise HTTPException(400, "name and path required")
    return {"response": create_share(payload), "error": None}

@router.post("/delete")
def api_delete(payload: dict = Body(...)):
    name = payload.get("name")
    if not name:
        raise HTTPException(400, "name required")
    return {"response": delete_share(name), "error": None}
