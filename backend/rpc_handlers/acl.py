# backend/rpc_handlers/acl.py
import logging
logger = logging.getLogger("mynas.rpc.acl")

from backend.app.permissions import (
    list_acls,
    set_acl_record,
    delete_acl_record,
)

def rpc_list(path: str):
    return [a for a in list_acls() if a["path"] == path]

def rpc_set(path: str, entries: list):
    result = []
    for entry in entries:
        result.append(
            set_acl_record(path, entry["user"], entry["permissions"])
        )
    return {"updated": result}

def rpc_remove(path: str, user: str):
    return delete_acl_record(path, user)

def register_rpc(register):
    register("acl", {
        "list": rpc_list,
        "set": rpc_set,
        "remove": rpc_remove,
    })
