# backend/rpc_handlers/shnfs.py
"""
RPC handlers for NFS-specific tasks.
Service: "nfs"
"""

from typing import Dict, Any, List

try:
    from app.utils.smb_nfs_ops import write_nfs_exports as _write_nfs_exports
except Exception:
    try:
        from app.nfs_utils import write_nfs_exports as _write_nfs_exports  # type: ignore
    except Exception:
        _write_nfs_exports = None

try:
    from app.share_manager import list_shares as _list_shares
except Exception:
    from backend.storage.share_manager import list_shares as _list_shares  # type: ignore

def rpc_write_exports() -> Dict[str, Any]:
    shares = _list_shares()
    nfs_shares = [s for s in shares if s.get("protocol") == "nfs"]
    if _write_nfs_exports is None:
        return {"status": "error", "reason": "nfs helper not available"}
    try:
        _write_nfs_exports(nfs_shares)
        return {"status": "ok", "written": len(nfs_shares)}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def rpc_list_shares() -> List[Dict[str, Any]]:
    return [s for s in _list_shares() if s.get("protocol") == "nfs"]

def register_rpc(register):
    register("nfs", {
        "write_exports": rpc_write_exports,
        "list_shares": rpc_list_shares
    })
