# backend/rpc_handlers/acl.py
"""
RPC handlers for ACLs. Service: "acl"
Methods: list / apply / remove
"""

from typing import Dict, Any, List

# prefer app.permissions
try:
    from app.permissions import list_acls as _list_acls, set_acl_record as _set_acl, delete_acl_record as _del_acl
except Exception:
    # fallback to app.acl_manager or backend.app.permissions
    try:
        from app.acl_manager import list_acls as _list_acls, apply_acl as _set_acl, remove_acl as _del_acl
    except Exception:
        from backend.app.permissions import list_acls as _list_acls, set_acl_record as _set_acl, delete_acl_record as _del_acl  # type: ignore

def rpc_list() -> List[Dict[str, Any]]:
    return _list_acls()

def rpc_apply(path: str, username: str, permissions: str) -> Dict[str, Any]:
    return _set_acl(path, username, permissions)

def rpc_remove(path: str, username: str) -> Dict[str, Any]:
    return _del_acl(path, username)

def register_rpc(register):
    register("acl", {
        "list": rpc_list,
        "apply": rpc_apply,
        "remove": rpc_remove,
    })
