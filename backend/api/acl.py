# backend/api/acl.py
from fastapi import APIRouter, HTTPException, Body
from backend.app.permissions import (
    list_acls,
    set_acl_record,
    delete_acl_record,
)

router = APIRouter()

@router.post("/list")
def api_list_acl(path: str):
    try:
        return {"response": [a for a in list_acls() if a["path"] == path], "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/set")
def api_set_acl(payload: dict = Body(...)):
    path = payload.get("path")
    entries = payload.get("entries")

    if not path or not entries:
        raise HTTPException(400, "path + entries required")

    res = []
    for entry in entries:
        res.append(set_acl_record(path, entry["user"], entry["permissions"]))

    return {"response": res, "error": None}

@router.post("/remove")
def api_remove_acl(payload: dict = Body(...)):
    path = payload.get("path")
    username = payload.get("user")

    if not path or not username:
        raise HTTPException(400, "path + user required")

    return {"response": delete_acl_record(path, username), "error": None}
