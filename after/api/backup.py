from fastapi import APIRouter, HTTPException
from backend.app.backup_manager import list_backups, create_config_backup, restore_config_backup, delete_config_backup

router = APIRouter()

@router.get("/")
def api_list_backups():
    return {"backups": list_backups()}

@router.post("/create")
def api_create_backup():
    name = create_config_backup()
    if not name: raise HTTPException(500, "could not create backup")
    return {"backup": name}

@router.post("/restore")
def api_restore(payload: dict):
    filename = payload.get("filename")
    ok = restore_config_backup(filename)
    if not ok: raise HTTPException(404, "backup not found")
    return {"restored": filename}

@router.delete("/")
def api_delete(filename: str):
    ok = delete_backup(filename)
    if not ok: raise HTTPException(404, "backup not found")
    return {"deleted": filename}
