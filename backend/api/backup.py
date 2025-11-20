from fastapi import APIRouter, Body, HTTPException
from backend.app.backup_manager import (
    list_backups, create_config_backup, restore_config_backup, delete_config_backup
)

router = APIRouter()

@router.post("/list")
def list_backups_api():
    return {"response": list_backups(), "error": None}

@router.post("/create")
def create_backup_api():
    return {"response": create_config_backup(), "error": None}

@router.post("/restore")
def restore_backup_api(payload: dict = Body(...)):
    fn = payload.get("filename")
    if not fn:
        raise HTTPException(400, "filename required")
    return {"response": restore_config_backup(fn), "error": None}

@router.post("/delete")
def delete_backup_api(payload: dict = Body(...)):
    fn = payload.get("filename")
    return {"response": delete_config_backup(fn), "error": None}
