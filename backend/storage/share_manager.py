# backend/storage/share_manager.py
"""
Share manager: SMB and NFS share management (best-effort).
Exposes:
 - list_shares()
 - create_smb_share(name, path, options)
 - create_nfs_share(name, path, options)
 - remove_share(name_or_uuid)
 - smb_status()
 - nfs_status()
 - load_shares()  # on startup
"""
import logging
import json
import shutil
import subprocess
from typing import List, Dict, Any

from backend.app.config_manager import cfg
try:
    from backend.realtime.websocket_server import WSManagerProxy
except Exception:
    WSManagerProxy = None

logger = logging.getLogger("mynas.share")

def list_shares() -> List[Dict[str, Any]]:
    return cfg.get("shares", [])

def create_smb_share(name: str, path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    entry = {"type": "smb", "name": name, "path": path, "options": options or {}}
    shares = cfg.get("shares", [])
    shares.append(entry)
    cfg.data["shares"] = shares
    cfg.save(cfg.data)
    if WSManagerProxy:
        try:
            WSManagerProxy.broadcast({"module": "shares", "event": "created", "share": entry})
        except Exception:
            pass
    # optionally call smbcontrol / samba-tool to apply config (not implemented here)
    return {"created": entry}

def create_nfs_share(name: str, path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    entry = {"type": "nfs", "name": name, "path": path, "options": options or {}}
    shares = cfg.get("shares", [])
    shares.append(entry)
    cfg.data["shares"] = shares
    cfg.save(cfg.data)
    if WSManagerProxy:
        try:
            WSManagerProxy.broadcast({"module": "shares", "event": "created", "share": entry})
        except Exception:
            pass
    # note: actually applying to /etc/exports is left to system integration
    return {"created": entry}

def remove_share(name_or_uuid: str) -> Dict[str, Any]:
    before = cfg.get("shares", [])
    after = [s for s in before if s.get("name") != name_or_uuid and s.get("uuid") != name_or_uuid and s.get("path") != name_or_uuid]
    cfg.data["shares"] = after
    cfg.save(cfg.data)
    if WSManagerProxy:
        try:
            WSManagerProxy.broadcast({"module": "shares", "event": "deleted", "name": name_or_uuid})
        except Exception:
            pass
    return {"removed": name_or_uuid}

def smb_status() -> Dict[str, Any]:
    # check samba service
    if shutil.which("smbstatus"):
        try:
            out = subprocess.check_output(["smbstatus"], text=True, stderr=subprocess.STDOUT)
            return {"smbstatus": out}
        except Exception as e:
            return {"error": str(e)}
    return {"smbstatus": "unavailable"}

def nfs_status() -> Dict[str, Any]:
    # best-effort: check exports or rpcinfo
    if shutil.which("exportfs"):
        try:
            out = subprocess.check_output(["exportfs", "-v"], text=True, stderr=subprocess.STDOUT)
            return {"exports": out}
        except Exception as e:
            return {"error": str(e)}
    return {"nfs": "unavailable"}

def load_shares():
    """
    Load all shares from config.json.
    OLD CODE:
        return cfg.get("shares", [])
    FIX:
        cfg.get_section("shares")
    """
    try:
        shares = cfg.get_section("shares") or []
        logger.info(f"Loaded {len(shares)} shares")
        return shares
    except Exception as e:
        logger.error(f"Failed loading shares: {e}")
        return []


def add_share(share_obj: dict):
    shares = cfg.get_section("shares") or []
    shares.append(share_obj)
    cfg.set_section("shares", shares)
    return True


def remove_share(name: str):
    shares = cfg.get_section("shares") or []
    new_list = [s for s in shares if s.get("name") != name]
    cfg.set_section("shares", new_list)
    return True
