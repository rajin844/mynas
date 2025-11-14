# backend/rpc_handlers/backup.py
from typing import Dict, Any, List

from backend.app.backup_manager import (
    list_backups as _list_backups,
    create_config_backup as _create_backup,
    restore_config_backup as _restore_backup,
    delete_config_backup as _delete_backup,
)

def rpc_list() -> List[str]:
    return _list_backups()

def rpc_create() -> Dict[str, Any]:
    return {"backup": _create_backup()}

def rpc_restore(filename: str) -> Dict[str, Any]:
    ok = _restore_backup(filename)
    return {"restored": filename} if ok else {"error": "not_found"}

def rpc_delete(filename: str) -> Dict[str, Any]:
    ok = _delete_backup(filename)
    return {"deleted": filename} if ok else {"error": "not_found"}

def register_rpc(register):
    register("backup", {
        "list": rpc_list,
        "create": rpc_create,
        "restore": rpc_restore,
        "delete": rpc_delete,
    })
