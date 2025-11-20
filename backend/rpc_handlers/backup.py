# backend/rpc_handlers/backup.py
from backend.system.backup_manager import list_backups, create_backup, restore_backup

def rpc_list():
    return list_backups()

def rpc_create():
    return create_backup()

def rpc_restore(file):
    return restore_backup(file)

def register_rpc(register):
    register("backup", {"list": rpc_list, "create": rpc_create, "restore": rpc_restore})
