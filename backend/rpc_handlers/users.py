# backend/rpc_handlers/users.py
from backend.system.user_manager import list_users, create_user, delete_user

def rpc_list():
    return list_users()

def rpc_create(meta):
    return create_user(meta)

def rpc_delete(username):
    return delete_user(username)

def register_rpc(register):
    register("users", {"list": rpc_list, "create": rpc_create, "delete": rpc_delete})
