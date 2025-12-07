# backend/storage/storage_manager.py
"""
Storage manager (MySQL-backed) - pools, disks, summary, pool create preview.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from backend.drivers.db import run_query  # async helper
from backend.app.safe_exec import safe_exec
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.storage")

# -------------------
# Disks
# -------------------
async def detect_disks() -> List[Dict[str, Any]]:
    """
    Discover system disks using lsblk (JSON) and upsert into DB.
    Returns list of disk dicts.
    """
    r = await safe_exec(["lsblk", "-J", "-o", "NAME,SIZE,MODEL,VENDOR,ROTA,TYPE,MOUNTPOINT"], timeout=8, sudo=True)
    if not r.get("ok"):
        logger.warning("lsblk failed: %s", r.get("stderr"))
        # fallback to reading DB
        rows = await run_query("SELECT * FROM disks", {})
        return [dict(row) for row in rows]
    try:
         j = json.loads(r["stdout"])
         disks_out = []
         for d in j.get("blockdevices", []):
                if d.get("type") != "disk": continue
                name = d.get("name")
                devpath = f"/dev/{name}"
                size = d.get("size")
                model = d.get("model")
                vendor = d.get("vendor")
                rot = True if d.get("rota") else False,
                mount = d.get("mountpoint")
                # upsert to DB
                await run_query("""
                INSERT INTO disks (name, devpath, size_text, model, vendor, rotational, mountpoint, updated_at)
                VALUES (:name, :devpath, :size, :model, :vendor, :rot, :mount, NOW())
                ON DUPLICATE KEY UPDATE size_text=VALUES(size_text), model=VALUES(model),
                vendor=VALUES(vendor), rotational=VALUES(rotational), mountpoint=VALUES(mountpoint), updated_at=NOW()
                """, {"name": name, "devpath": devpath, "size": size, "model": model, "vendor": vendor, "rot": rot, "mount": mount})
                disks_out.append({"name": name, "devpath": devpath, "size": size, "model": model, "vendor": vendor, "rotational": bool(rot), "mountpoint": mount})
         await WSManagerProxy.broadcast({"module":"storage","event":"disks_updated","disks":disks_out})
         return disks_out

    except Exception as e:
        logger.exception("parse lsblk error: %s", e)
        rows = await run_query("SELECT * FROM disks", {})
        return [dict(row) for row in rows]


async def list_disks() -> List[Dict[str, Any]]:
    rows = await run_query("SELECT name, devpath, size_text AS size, model, vendor, rotational, mountpoint FROM disks ORDER BY name", {})
    return [dict(r) for r in rows]


# -------------------
# Storage summary
# -------------------
async def get_storage_summary() -> Dict[str, Any]:
    # pools, datasets counts, total capacity rough
    pools = await run_query("SELECT name, type, health, capacity_pct FROM pools ORDER BY id DESC", {})
    datasets = await run_query("SELECT pool, name, mountpoint FROM datasets ORDER BY id DESC", {})
    disks = await run_query("SELECT name, devpath, size_text, model, vendor, rotational FROM disks ORDER BY name", {})

    # compute total size approximate (not numeric parse, keep text for now)
    total_capacity = None
    total_bytes = sum(d.get("size_bytes") or 0 for d in disks)
    # build simple dict
    return {
        "pools": [dict(p) for p in pools],
        "datasets": [dict(d) for d in datasets],
        "disks": [dict(d) for d in disks],
        "total_capacity": total_bytes
    }

# -------------------
# Pool create / destroy
# -------------------
async def preview_create_pool(name: str, devices: List[str], raidz: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns a preview describing the plan (vdev layout, estimated usable).
    """
    # Basic preview using counts; a separate raidz_builder module should be used for more detail
    mode = raidz or "single"
    vdevs = [{"type": mode, "devices": devices}]
    # estimate (placeholder)
    return {"name": name, "vdevs": vdevs, "estimated": {"usable": "depends"}}

async def create_zfs_pool(name: str, devices: List[str], raidz: Optional[str] = None, dry_run: bool = True, force: bool = False) -> Dict[str, Any]:
    """
    Create pool (dry_run shows preview)
    """
    if dry_run:
        return await preview_create_pool(name, devices, raidz)

    # Build zpool create command
    cmd = ["zpool", "create"]
    if force:
        cmd.append("-f")
    if raidz and raidz.startswith("raidz"):
        # naive: zpool create <name> raidz1 /dev/sda /dev/sdb ...
        cmd.append(name)
        cmd.append(raidz)
        cmd += devices
    elif raidz == "mirror":
        cmd.append(name)
        cmd.append("mirror")
        cmd += devices
    else:
        # single vdevs
        cmd.append(name)
        cmd += devices

    r = await safe_exec(cmd, timeout=120, sudo=True)
    if not r.get("ok"):
        raise RuntimeError(r.get("stderr"))

    # On success, insert pool record into DB (basic)
    await run_query(
        "INSERT INTO pools (name, type, devices, health, created_at) VALUES (:name, :type, :devices, :health, NOW())",
        {"name": name, "type": "zfs", "devices": ",".join(devices), "health": "ONLINE"}
    )

    # broadcast
    await WSManagerProxy.broadcast({"module": "zfs", "event": "pool_created", "pool": name})

    return {"ok": True, "name": name}
