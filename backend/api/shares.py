from fastapi import APIRouter, Body
from backend.storage.share_manager import list_shares, add_share, remove_share, update_share

router = APIRouter()

@router.post("/list")
def list_all():
    return {"response": list_shares(), "error": None}

@router.post("/add")
def add(payload: dict = Body(...)):
    return {"response": add_share(**payload), "error": None}

@router.post("/remove")
def remove(payload: dict = Body(...)):
    return {"response": remove_share(payload["name"]), "error": None}
