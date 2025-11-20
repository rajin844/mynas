# backend/storage/snapshot_manager.py
"""
Snapshot manager: list/create/destroy/rollback/clone snapshots
Uses zfs snapshots when available; otherwise uses config store.
"""
import shutil
import subprocess
import logging
import time
from typing import List, Dict, Any

from backend.app.config_manager import cfg
try:
    from backend.realtime.websocket_server import WSManagerProxy
except Exception:
    WSManagerProxy = None

logger = logging.getLogger("mynas.snapshot")

def _has_cmd(name: str) -> bool:
    return shutil.which(name) is not None

def list_snapshots(dataset: str = None) -> List[Dict[str, Any]]:
    """Return snapshots from zfs or config store."""
    if _has_cmd("zfs"):
        try:
            args = ["zfs", "list", "-t", "snapshot", "-H", "-o", "name,creation"]
            if dataset:
                args += ["-r", dataset]
            out = subprocess.check_output(args, text=True)
            snaps = []
            for ln in out.strip().splitlines():
                name, creation = ln.split()[:2]
                snaps.append({"name": name, "creation": creation})
            return snaps
        except Exception as e:
            logger.debug("zfs snapshot list failed: %s", e)
    # fallback
    return cfg.get("snapshots", [])

def create_snapshot(dataset: str, name: str) -> Dict[str, Any]:
    snapname = f"{dataset}@{name}"
    if _has_cmd("zfs"):
        try:
            out = subprocess.check_output(["zfs", "snapshot", snapname], stderr=subprocess.STDOUT, text=True)
            # persist minimal snapshot info
            snaps = cfg.data.setdefault("snapshots", [])
            snaps.append({"dataset": dataset, "name": name, "ts": int(time.time())})
            cfg.save(cfg.data)
            if WSManagerProxy:
                try:
                    WSManagerProxy.broadcast({"module": "snap", "event": "created", "snapshot": snapname})
                except Exception:
                    pass
            return {"success": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("snapshot create failed: %s", e)
            return {"success": False, "error": str(e)}
    # emulate
    snaps = cfg.data.setdefault("snapshots", [])
    snaps.append({"dataset": dataset, "name": name, "ts": int(time.time())})
    cfg.save(cfg.data)
    return {"success": True, "emulated": True}

def destroy_snapshot(dataset: str, name: str) -> Dict[str, Any]:
    snapname = f"{dataset}@{name}"
    if _has_cmd("zfs"):
        try:
            out = subprocess.check_output(["zfs", "destroy", snapname], stderr=subprocess.STDOUT, text=True)
            # remove from config if present
            snaps = [s for s in cfg.data.get("snapshots", []) if not (s.get("dataset") == dataset and s.get("name") == name)]
            cfg.data["snapshots"] = snaps
            cfg.save(cfg.data)
            return {"success": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("snapshot destroy failed: %s", e); return {"success": False, "error": str(e)}
    # emulate
    snaps = [s for s in cfg.data.get("snapshots", []) if not (s.get("dataset") == dataset and s.get("name") == name)]
    cfg.data["snapshots"] = snaps
    cfg.save(cfg.data)
    return {"success": True, "emulated": True}

def rollback_snapshot(dataset: str, name: str, force: bool = False) -> Dict[str, Any]:
    snapname = f"{dataset}@{name}"
    if _has_cmd("zfs"):
        try:
            cmd = ["zfs", "rollback"]
            if force:
                cmd.append("-r")
            cmd.append(snapname)
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            return {"success": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("rollback failed: %s", e); return {"success": False, "error": str(e)}
    return {"success": False, "error": "zfs not available"}

def clone_snapshot(dataset: str, name: str, target: str) -> Dict[str, Any]:
    snapname = f"{dataset}@{name}"
    if _has_cmd("zfs"):
        try:
            out = subprocess.check_output(["zfs", "clone", snapname, target], stderr=subprocess.STDOUT, text=True)
            return {"success": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("clone failed: %s", e); return {"success": False, "error": str(e)}
    return {"success": False, "error": "zfs not available"}
