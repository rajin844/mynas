# backend/rpc_handlers/shsamba.py
"""
RPC handlers for Samba-specific tasks.
Service: "samba"
"""

from typing import Dict, Any, List

# Prefer app.utils.smb_nfs_ops or app.samba_utils
try:
    from app.utils.smb_nfs_ops import write_smb_conf as _write_smb_conf
except Exception:
    try:
        from app.samba_utils import write_smb_conf as _write_smb_conf  # type: ignore
    except Exception:
        _write_smb_conf = None

# use share manager to get current shares
try:
    from app.share_manager import list_shares as _list_shares
except Exception:
    from backend.storage.share_manager import list_shares as _list_shares  # type: ignore

def rpc_write_config() -> Dict[str, Any]:
    shares = _list_shares()
    if _write_smb_conf is None:
        return {"status": "error", "reason": "smb helper not available"}
    try:
        _write_smb_conf([s for s in shares if s.get("protocol") == "smb"])
        return {"status": "ok", "written": len([s for s in shares if s.get("protocol") == "smb"])}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def rpc_list_shares() -> List[Dict[str, Any]]:
    return [s for s in _list_shares() if s.get("protocol") == "smb"]

def register_rpc(register):
    register("samba", {
        "write_config": rpc_write_config,
        "list_shares": rpc_list_shares
    })
