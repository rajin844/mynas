# backend/rpc_handlers/acl.py
from backend.app.permissions import list_acls, set_acl_record, delete_acl_record

def rpc_list():
    return list_acls()

def rpc_apply(path: str, username: str, permissions: str):
    return set_acl_record(path, username, permissions)

def rpc_set(path, acl):
    return set_acl(path, acl)

def rpc_remove(path, username):
    return remove_acl(path, username)

def register_rpc(register):
    register("acl", {"list": rpc_list, "set": rpc_set, "remove": rpc_remove})    

def register_rpc(register):
    register("acl", {
        "list": rpc_list,
        "apply": rpc_apply,
        "remove": rpc_remove,
    })
