                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      # backend/storage/storage_manager.py
"""
Storage manager: disk enumeration, SMART, disk usage, storage summary.

Functions:
 - list_disks()
 - detect_disks()
 - smart_health(dev)
 - smart_test(dev, test_type="short")
 - disk_usage(dev)
 - get_storage_summary()
"""
import shutil
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from backend.app.config_manager import cfg
try:
    from backend.realtime.websocket_server import WSManagerProxy
except Exception:
    WSManagerProxy = None

logger = logging.getLogger("mynas.storage")

def _has_cmd(name: str) -> bool:
    return shutil.which(name) is not None

def list_disks() -> List[Dict[str, Any]]:
    """Return list of block devices. Uses lsblk -J when available, else config fallback."""
    if _has_cmd("lsblk"):
        try:
            out = subprocess.check_output(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL,VENDOR,ROTA"], text=True)
            data = json.loads(out)
            disks = []
            for d in data.get("blockdevices", []):
                if d.get("type") in ("disk",):
                    disks.append({
                        "name": d.get("name"),
                        "devpath": f"/dev/{d.get('name')}",
                        "size": d.get("size"),
                        "mountpoint": d.get("mountpoint"),
                        "model": d.get("model"),
                        "vendor": d.get("vendor"),
                        "rotational": d.get("rota"),
                    })
            # persist candidate disk inventory
            cfg.data.setdefault("storage", {})["disks"] = disks
            cfg.save(cfg.data)
            return disks
        except Exception as e:
            logger.exception("lsblk failed: %s", e)

    # fallback to saved config
    return cfg.get("storage", {}).get("disks", [])

def detect_disks() -> Dict[str, Any]:
    """Run disk detection and broadcast result."""
    disks = list_disks()
    result = {"count": len(disks), "disks": disks}
    try:
        if WSManagerProxy:
            WSManagerProxy.broadcast({"module": "storage", "event": "disks_detected", "count": len(disks)})
    except Exception:
        pass
    return result

def disk_usage(dev: str) -> Dict[str, Any]:
    """Return filesystem usage for a device (best-effort)."""
    # Try lsblk for FSUSED/FSUSE%; fallback to zeroes
    if _has_cmd("lsblk"):
        try:
            out = subprocess.check_output(["lsblk", "-b", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL,VENDOR,FSTYPE,FSUSED,FSUSE%", dev], text=True)
            # parse lines
            lines = [l for l in out.strip().splitlines() if l.strip()]
            if len(lines) >= 2:
                parts = lines[1].split()
                # best-effort mapping
                size = parts[1] if len(parts) > 1 else "0"
                used = parts[-2] if len(parts) > 2 else "0"
                pct = parts[-1] if len(parts) > 2 else "0%"
                return {"device": dev, "size": int(size) if size.isdigit() else size, "used": int(used) if str(used).isdigit() else used, "percent": pct}
        except Exception as e:
            logger.debug("lsblk disk_usage parse failed: %s", e)

    return {"device": dev, "size": 0, "used": 0, "percent": "0%"}

def smart_health(dev: str) -> Dict[str, Any]:
    """Return a light summary of SMART health. Requires smartctl."""
    if not _has_cmd("smartctl"):
        return {"supported": False, "message": "smartctl not installed"}
    try:
        out = subprocess.check_output(["smartctl", "-H", "-i", dev], text=True, stderr=subprocess.STDOUT)
        return {"supported": True, "output": out}
    except subprocess.CalledProcessError as e:
        return {"supported": True, "success": False, "output": getattr(e, "output", str(e))}
    except Exception as e:
        logger.exception("smartctl failed: %s", e)
        return {"supported": False, "error": str(e)}

def smart_test(dev: str, test_type: str = "short") -> Dict[str, Any]:
    """Start a SMART test (short/long/conveyance) if smartctl present."""
    if not _has_cmd("smartctl"):
        return {"supported": False, "message": "smartctl not installed"}
    try:
        cmd = ["smartctl", "-t", test_type, dev]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        return {"started": True, "cmd": " ".join(cmd), "output": out}
    except Exception as e:
        logger.exception("smart test failed: %s", e)
        return {"started": False, "error": str(e)}

def get_storage_summary() -> Dict[str, Any]:
    storage = cfg.get_storage()
    pools = storage.get("pools", [])
    datasets = storage.get("datasets", [])
    disks = list_disks()
    total_used = 0
    total = 0
    for d in disks:
        u = d.get("usage", {})
        if u and u.get("total"):
            total_used += u.get("used", 0)
            total += u.get("total", 0)
    percent = (total_used / total * 100) if total else 0
    return {
        "pools": pools,
        "datasets": datasets,
        "disks": disks,
        "capacity_percent": round(percent, 2)
    }