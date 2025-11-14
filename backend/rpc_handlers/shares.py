# backend/rpc_handlers/shares.py
from typing import Dict, Any, List

try:
    from backend.storage.share_manager import list_shares as _list_shares, add_share as _add_share, remove_share as _remove_share, update_share as _update_share, sync_shares_with_system as _sync
except Exception:
    from backend.storage.share_manager import list_shares as _list_shares, add_share as _add_share, remove_share as _remove_share, update_share as _update_share, sync_shares_with_system as _sync  # type: ignore

def rpc_list() -> List[Dict[str, Any]]:
    return _list_shares()

def rpc_add(name: str, path: str, protocol: str = "smb", readonly: bool = False, comment: str = "") -> Dict[str, Any]:
    return _add_share(name, path, protocol, readonly, comment)

def rpc_remove(name: str) -> Dict[str, Any]:
    return _remove_share(name)

def rpc_update(name: str, updates: dict) -> Dict[str, Any]:
    return _update_share(name, updates)

def rpc_sync_system() -> Dict[str, Any]:
    try:
        return _sync()
    except Exception:
        return {"status": "error", "reason": "sync not implemented"}

def register_rpc(register):
    register("shares", {
        "list": rpc_list,
        "add": rpc_add,
        "remove": rpc_remove,
        "update": rpc_update,
        "sync": rpc_sync_system,
    })
