# backend/api/users.py
from fastapi import APIRouter, HTTPException, Body

router = APIRouter()

@router.post("/listusers")
def api_users_list():
    return {"response": cfg.list_users(), "error": None}

@router.post("/add")
def api_add_user(payload: dict = Body(...)):
    if not payload.get("username"):
        raise HTTPException(400, "username required")

    cfg.add_user(payload)
    return {"response": True, "error": None}

@router.post("/delete")
def api_delete_user(username: str):
    cfg.remove_user(username)
    return {"response": True, "error": None}
