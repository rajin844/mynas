# backend/storage/zfs_manager.py
"""
ZFS manager: list/create/destroy pools, datasets, import/export, scrub, status.
Functions implemented:
 - list_pools()
 - pool_status(name)
 - pool_health(name)
 - pool_topology(name)
 - create_pool(name, devices, raidz=None, force=False, dryRun=True)
 - destroy_pool(name, force=False)
 - import_pool(name)
 - export_pool(name)
 - scrub_pool(pool)
 - scrub_status(pool)
 - list_datasets(pool=None)
 - create_dataset(pool, name, mountpoint=None, dryRun=True)
 - destroy_dataset(pool, name)
"""
import shutil
import subprocess
import logging
from typing import List, Dict, Any, Optional

from backend.app.config_manager import cfg
try:
    from backend.realtime.websocket_server import WSManagerProxy
except Exception:
    WSManagerProxy = None

logger = logging.getLogger("mynas.zfs")

def _has_cmd(name: str) -> bool:
    return shutil.which(name) is not None

# ----------------------
# Pools & Datasets (query)
# ----------------------
def list_pools() -> List[Dict[str, Any]]:
    """Return list of pools using zpool if available, else config fallback"""
    if _has_cmd("zpool"):
        try:
            out = subprocess.check_output(["zpool", "list", "-H", "-o", "name,size,alloc,free,health"], text=True)
            pools = []
            for ln in out.strip().splitlines():
                parts = ln.split()
                pools.append({
                    "name": parts[0],
                    "size": parts[1] if len(parts) > 1 else "",
                    "alloc": parts[2] if len(parts) > 2 else "",
                    "free": parts[3] if len(parts) > 3 else "",
                    "health": parts[4] if len(parts) > 4 else "",
                })
            return pools
        except Exception as e:
            logger.exception("zpool list failed: %s", e)

    return cfg.get("storage", {}).get("pools", [])

def pool_status(name: str) -> Dict[str, Any]:
    """Return full zpool status if zpool present, else best-effort"""
    if _has_cmd("zpool"):
        try:
            out = subprocess.check_output(["zpool", "status", name], text=True, stderr=subprocess.STDOUT)
            return {"name": name, "status": out}
        except subprocess.CalledProcessError as e:
            return {"name": name, "error": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("zpool status failed: %s", e)

    # fallback
    pools = list_pools()
    for p in pools:
        if p.get("name") == name:
            return p
    return {"name": name, "error": "not found"}

def pool_health(name: str) -> Dict[str, Any]:
    """Return health string and color hint"""
    pools = list_pools()
    for p in pools:
        if p.get("name") == name:
            h = str(p.get("health", "UNKNOWN")).upper()
            color = "green" if h in ("ONLINE", "HEALTHY") else ("red" if h in ("DEGRADED","FAULTED","OFFLINE","UNAVAIL") else "yellow")
            return {"name": name, "health": h, "color": color}
    return {"name": name, "health": "UNKNOWN", "color": "gray"}

def pool_topology(name: str) -> Dict[str, Any]:
    """Return a simple parsed topology (best-effort)."""
    if _has_cmd("zpool"):
        try:
            out = subprocess.check_output(["zpool", "status", "-v", name], text=True, stderr=subprocess.STDOUT)
            # Return raw text for now; UI can parse
            return {"name": name, "topology": out}
        except Exception as e:
            logger.debug("pool_topology failed: %s", e)
    return {"name": name, "topology": "unavailable"}

# ----------------------
# Create / Destroy Pool
# ----------------------
def create_pool(name: str, devices: List[str], raidz: Optional[str] = None, force: bool = False, dryRun: bool = True) -> Dict[str, Any]:
    """
    Create a zpool. If dryRun True attempt zpool -n or synthesize a preview.
    raidz may be "raidz1"/"raidz2"/"raidz3" or "mirror"/"stripe"
    """
    # sanitize device list
    devices = list(devices or [])
    if not devices:
        return {"success": False, "error": "no devices"}

    if _has_cmd("zpool"):
        base_cmd = ["zpool", "create"]
        if force:
            base_cmd.append("-f")
        # dry-run using -n
        if dryRun:
            cmd = base_cmd + ["-n", name] + ( [raidz] + devices if raidz else devices )
        else:
            cmd = base_cmd + ([name] + ( [raidz] + devices if raidz else devices))

        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            result = {"success": True, "dryRun": dryRun, "cmd": " ".join(cmd), "output": out}
            if not dryRun:
                # persist to config
                store = cfg.get("storage", {})
                pools = store.get("pools", [])
                pools.append({"name": name, "devices": devices, "raidz": raidz})
                store["pools"] = pools
                cfg.update_storage(store)
                if WSManagerProxy:
                    try:
                        WSManagerProxy.broadcast({"module": "zfs", "event": "pool_created", "name": name})
                    except Exception:
                        pass
            return result
        except subprocess.CalledProcessError as e:
            return {"success": False, "cmd": " ".join(cmd), "output": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("zpool create failed: %s", e)
            return {"success": False, "error": str(e)}

    # zpool not present => emulate preview or persist
    if dryRun:
        return {"success": True, "dryRun": True, "cmd": f"emulated zpool create {name} ...", "estimated": {"devices": devices}}
    # persist emulated pool
    store = cfg.get("storage", {})
    pools = store.get("pools", [])
    pools.append({"name": name, "devices": devices, "raidz": raidz})
    store["pools"] = pools
    cfg.update_storage(store)
    if WSManagerProxy:
        try:
            WSManagerProxy.broadcast({"module": "zfs", "event": "pool_created", "name": name})
        except Exception:
            pass
    return {"success": True, "dryRun": False, "cmd": "emulated create"}

def destroy_pool(name: str, force: bool = False) -> Dict[str, Any]:
    """Destroy a pool (destructive)."""
    if _has_cmd("zpool"):
        cmd = ["zpool", "destroy"] + (["-f"] if force else []) + [name]
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            # remove from config if present
            store = cfg.get("storage", {})
            store["pools"] = [p for p in store.get("pools", []) if p.get("name") != name]
            cfg.update_storage(store)
            if WSManagerProxy:
                try:
                    WSManagerProxy.broadcast({"module": "zfs", "event": "pool_destroyed", "name": name})
                except Exception:
                    pass
            return {"success": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("zpool destroy failed: %s", e)
            return {"success": False, "error": str(e)}
    # emulate
    store = cfg.get("storage", {})
    store["pools"] = [p for p in store.get("pools", []) if p.get("name") != name]
    cfg.update_storage(store)
    return {"success": True, "emulated": True}

# ----------------------
# Import / Export
# ----------------------
def import_pool(name: str) -> Dict[str, Any]:
    if _has_cmd("zpool"):
        try:
            out = subprocess.check_output(["zpool", "import", name], stderr=subprocess.STDOUT, text=True)
            return {"imported": name, "output": out}
        except Exception as e:
            logger.exception("zpool import failed: %s", e)
            return {"error": str(e)}
    # emulated import
    return {"imported": name, "emulated": True}

def export_pool(name: str) -> Dict[str, Any]:
    if _has_cmd("zpool"):
        try:
            out = subprocess.check_output(["zpool", "export", name], stderr=subprocess.STDOUT, text=True)
            return {"exported": name, "output": out}
        except Exception as e:
            logger.exception("zpool export failed: %s", e)
            return {"error": str(e)}
    # emulated
    return {"exported": name, "emulated": True}

# ----------------------
# Scrub
# ----------------------
def scrub_pool(pool: str) -> Dict[str, Any]:
    if _has_cmd("zpool"):
        try:
            out = subprocess.check_output(["zpool", "scrub", pool], stderr=subprocess.STDOUT, text=True)
            return {"started": pool, "output": out}
        except Exception as e:
            logger.exception("zpool scrub failed: %s", e)
            return {"error": str(e)}
    return {"started": pool, "emulated": True}

def scrub_status(pool: str) -> Dict[str, Any]:
    if _has_cmd("zpool"):
        try:
            out = subprocess.check_output(["zpool", "status", pool], stderr=subprocess.STDOUT, text=True)
            # quick parse: scan: line contains progress
            scan_lines = [l for l in out.splitlines() if "scan:" in l.lower()]
            return {"pool": pool, "scan": "\n".join(scan_lines) if scan_lines else "none", "raw": out}
        except Exception as e:
            logger.exception("zpool status (scrub) failed: %s", e)
            return {"error": str(e)}
    return {"pool": pool, "scan": "unavailable", "emulated": True}

# ----------------------
# Datasets
# ----------------------
def list_datasets(pool: Optional[str] = None) -> List[Dict[str, Any]]:
    if _has_cmd("zfs"):
        try:
            args = ["zfs", "list", "-H", "-o", "name,mountpoint,used,avail"]
            if pool:
                args += ["-r", pool]
            out = subprocess.check_output(args, text=True)
            ds = []
            for ln in out.strip().splitlines():
                parts = ln.split()
                ds.append({"name": parts[0], "mountpoint": parts[1] if len(parts) > 1 else "", "used": parts[2] if len(parts) > 2 else "", "avail": parts[3] if len(parts) > 3 else ""})
            return ds
        except Exception as e:
            logger.exception("zfs list failed: %s", e)

    return cfg.get("storage", {}).get("datasets", [])

def create_dataset(pool: str, name: str, mountpoint: Optional[str] = None, dryRun: bool = True) -> Dict[str, Any]:
    fullname = f"{pool}/{name}"
    if _has_cmd("zfs"):
        try:
            cmd = ["zfs", "create"]
            if dryRun:
                cmd = ["zfs", "create", "-n", fullname]
                if mountpoint:
                    cmd += ["-o", f"mountpoint={mountpoint}"]
            else:
                if mountpoint:
                    cmd += ["-o", f"mountpoint={mountpoint}", fullname]
                else:
                    cmd += [fullname]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            if not dryRun:
                store = cfg.get("storage", {})
                ds = store.get("datasets", [])
                ds.append({"pool": pool, "name": name, "mountpoint": mountpoint})
                store["datasets"] = ds
                cfg.update_storage(store)
                if WSManagerProxy:
                    try:
                        WSManagerProxy.broadcast({"module": "zfs", "event": "dataset_created", "name": fullname})
                    except Exception:
                        pass
            return {"success": True, "dryRun": dryRun, "cmd": " ".join(cmd), "output": out}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("zfs create failed: %s", e)
            return {"success": False, "error": str(e)}
    # not available: emulate
    if dryRun:
        return {"success": True, "dryRun": True, "cmd": f"emulated zfs create -n {fullname}"}
    store = cfg.get("storage", {})
    ds = store.get("datasets", [])
    ds.append({"pool": pool, "name": name, "mountpoint": mountpoint})
    store["datasets"] = ds
    cfg.update_storage(store)
    return {"success": True, "emulated": True}

def destroy_dataset(pool: str, name: str) -> Dict[str, Any]:
    fullname = f"{pool}/{name}"
    if _has_cmd("zfs"):
        try:
            out = subprocess.check_output(["zfs", "destroy", fullname], stderr=subprocess.STDOUT, text=True)
            # remove from config
            store = cfg.get("storage", {})
            store["datasets"] = [d for d in store.get("datasets", []) if not (d.get("pool") == pool and d.get("name") == name)]
            cfg.update_storage(store)
            if WSManagerProxy:
                try:
                    WSManagerProxy.broadcast({"module": "zfs", "event": "dataset_destroyed", "name": fullname})
                except Exception:
                    pass
            return {"success": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": getattr(e, "output", str(e))}
        except Exception as e:
            logger.exception("zfs destroy failed: %s", e)
            return {"success": False, "error": str(e)}
    # emulate
    store = cfg.get("storage", {})
    store["datasets"] = [d for d in store.get("datasets", []) if not (d.get("pool") == pool and d.get("name") == name)]
    cfg.update_storage(store)
    return {"success": True, "emulated": True}
