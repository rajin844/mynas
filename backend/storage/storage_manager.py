import os
import subprocess
from fastapi import HTTPException
from typing import List, Dict
from backend.app.config_manager import ConfigManager
from backend.app.utils.zfs_ops import (
    PoolInfo,
    DatasetInfo,
    zpool_list,
    zpool_import_list,
    create_pool,
    destroy_pool,
    import_pool,
)
from backend.realtime.events import emit_event

cfg = ConfigManager()

"""
Storage Manager
Detects and manages disks, filesystems, and ZFS pools/datasets.
"""

# ------------------------------
# Disk Detection and Info
# ------------------------------

def detect_disks() -> List[str]:
    """Detect available block devices (non-partition)."""
    disks: List[str] = []
    try:
        output = subprocess.check_output(["lsblk", "-dn", "-o", "NAME,TYPE"]).decode()
        for line in output.splitlines():
            name, typ = line.split()
            if typ == "disk":
                disks.append(f"/dev/{name}")
    except Exception as e:
        print(f"[ERROR] Failed to detect disks: {e}")
    return disks


def disk_info(disk: str) -> Dict:
    """Return dictionary with disk size, partitions, and mount points."""
    info = {"disk": disk, "partitions": []}
    try:
        output = subprocess.check_output(["lsblk", "-o", "NAME,SIZE,MOUNTPOINT", disk]).decode()
        lines = output.splitlines()[1:]
        for l in lines:
            parts = l.split()
            if not parts:
                continue
            entry = {
                "name": parts[0],
                "size": parts[1],
                "mountpoint": parts[2] if len(parts) > 2 else None,
            }
            info["partitions"].append(entry)
    except Exception as e:
        print(f"[ERROR] Failed to get disk info for {disk}: {e}")
    return info


def list_filesystems() -> Dict[str, str]:
    """Return dictionary of filesystem types per disk/partition."""
    fsmap: Dict[str, str] = {}
    try:
        output = subprocess.check_output(["blkid"]).decode()
        for line in output.splitlines():
            parts = line.split(":")
            if len(parts) < 2:
                continue
            dev = parts[0]
            if 'TYPE="' in line:
                fs_type = line.split('TYPE="')[1].split('"')[0]
                fsmap[dev] = fs_type
    except Exception as e:
        print(f"[WARN] blkid not available or failed: {e}")
    return fsmap


def mount_disk(disk: str, path: str) -> bool:
    """Mount disk to path."""
    try:
        os.makedirs(path, exist_ok=True)
        subprocess.run(["mount", disk, path], check=False)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to mount {disk} to {path}: {e}")
        return False


# ------------------------------
# ZFS Pool Management
# ------------------------------

def list_pools() -> Dict[str, List[PoolInfo]]:
    """
    Return:
    {
        "config_pools": [...],
        "zpool_list": [...],
        "importable_pools": [...]
    }
    """
    stored = cfg.get_section("storage") or {}
    return {
        "config_pools": stored.get("pools", []),
        "zpool_list": zpool_list(),
        "importable_pools": zpool_import_list(),
    }


def create_pool_api(name: str, devices: List[str]) -> Dict[str, bool]:
    """Create ZFS pool and record in config.json."""
    if not name or not devices:
        raise HTTPException(status_code=400, detail="Pool name and devices required")

    ok = create_pool(name, devices)
    if ok:
        storage = cfg.get_section("storage") or {}
        pools = storage.get("pools", [])
        pools.append({"name": name, "devices": devices})
        storage["pools"] = pools
        cfg.set_section("storage", storage)
        emit_event({"module": "storage", "action": "pool_created", "name": name})
    return {"ok": ok}


def import_pool_api(name: str) -> Dict[str, bool]:
    """Import existing ZFS pool."""
    if not name:
        raise HTTPException(status_code=400, detail="Pool name required")

    ok = import_pool(name)
    if ok:
        emit_event({"module": "storage", "action": "pool_imported", "name": name})
    return {"ok": ok}


def destroy_pool_api(name: str) -> Dict[str, bool]:
    """Destroy pool and update config.json."""
    if not name:
        raise HTTPException(status_code=400, detail="Pool name required")

    ok = destroy_pool(name)
    if ok:
        storage = cfg.get_section("storage") or {}
        pools = [p for p in storage.get("pools", []) if p.get("name") != name]
        storage["pools"] = pools
        cfg.set_section("storage", storage)
        emit_event({"module": "storage", "action": "pool_deleted", "name": name})
    return {"ok": ok}
