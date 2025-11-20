# backend/rpc_handlers/users.py
import logging
logger = logging.getLogger("mynas.rpc.users")

from backend.app.config_manager import cfg

def rpc_list():
    return cfg.list_users()

def rpc_add(username: str, role: str, password: str):
    cfg.add_user({"username": username, "role": role, "password": password})
    return {"status": "added", "user": username}

def rpc_delete(username: str):
    cfg.remove_user(username)
    return {"status": "deleted", "user": username}


def register_rpc(register):
    register("users", {
        "list": rpc_list,
        "add": rpc_add,
        "delete": rpc_delete,
    })
