from fastapi import APIRouter, Body, HTTPException
from backend.app.backup_manager import (
    list_backups, create_config_backup, restore_config_backup, delete_config_backup
)

router = APIRouter()

@router.post("/list")
def api_list():
    return {"response": list_backups(), "error": None}

@router.post("/create")
def api_create():
    return {"response": create_backup(), "error": None}

@router.post("/restore")
def api_restore(payload: dict = Body(...)):
    file = payload.get("file")
    if not file:
        raise HTTPException(400, "file required")
    return {"response": restore_backup(file), "error": None}

@router.post("/delete")
def delete_backup_api(payload: dict = Body(...)):
    fn = payload.get("filename")
    return {"response": delete_config_backup(fn), "error": None}
