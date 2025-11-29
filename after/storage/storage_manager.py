# backend/storage/storage_manager.py
"""
Storage manager (DB-backed)
- detect_disks() -> probe system disks (uses lsblk or fallback)
- list_disks() -> read from DB table `disks` (if present) or return probe
- get_storage_summary() -> pools/datasets/disks summary (from DB)
- create_zfs_pool() -> preview or actually create pool (uses zfs_manager)
- destroy_zfs_pool(), import_pool()
Broadcasts WS events on changes.
"""

import json
import logging
import shutil
from typing import List, Dict, Any, Optional
from backend.storage.storage_driver import get_storage_driver
from backend.storage import zfs_driver
from backend.storage.raidz_manager import build_raidz_layout
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.storage_manager")


# -------------------------
# Disk detection (simple)
# -------------------------
def human_size(num: int) -> str:
    for unit in ["B", "K", "M", "G", "T", "P"]:
        if num < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}E"


# -------------------------------------------------------
# LIST DISKS (DB → API READY)
# -------------------------------------------------------
async def list_disks_out() -> List[Dict[str, Any]]:
    disks = await list_disks_db()
    for d in disks:
        d["size_human"] = human_size(d.get("size_bytes", 0))
    return disks


async def detect_disks() -> List[Dict[str, Any]]:
    """
    Detect disks using lsblk -J -b safely and store/update in DB.
    Returns final DB records.
    """

    # --------------------------------------------------------
    # 1) Run lsblk safely
    # --------------------------------------------------------
    r = await safe_exec(["lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE,MODEL,VENDOR,ROTA"], timeout=10)

    if not r.get("ok"):
        logger.warning("lsblk failed: %s", r.get("stderr"))
        return await list_disks_out()

    # --------------------------------------------------------
    # 2) Parse JSON safely
    # --------------------------------------------------------
    try:
        obj = json.loads(r.get("stdout", "{}"))
        devices = obj.get("blockdevices", [])
    except Exception as e:
        logger.error("JSON decode error: %s", e)
        return await list_disks_out()

    detected = []

    # --------------------------------------------------------
    # 3) Handle each disk
    # --------------------------------------------------------
    for d in devices:

        # Ignore non-disk devices
        if d.get("type") not in ("disk", "nvme"):
            continue

        # Safe integer size
        try:
            size_bytes = int(d.get("size") or 0)
        except:
            size_bytes = 0

        # ROTA may be missing OR string OR boolean
        rota = d.get("rota")
        if isinstance(rota, str):
            rota = rota.lower() in ("1", "true", "yes")
        elif rota is None:
            rota = False  # default SSD
        elif isinstance(rota, int):
            rota = rota == 1

        rec = {
            "name": d.get("name"),
            "devpath": f"/dev/{d.get('name')}",
            "model": d.get("model") or "Unknown",
            "vendor": d.get("vendor") or "Unknown",
            "size_bytes": int(d.get("size") or 0),
            "rotational": True if d.get("rota") else False,
            "mountpoint": d.get("mountpoint"),
        }

        await add_or_update_disk(rec)
        

    return await list_disks_out()



# -------------------------
# Storage Summary
# -------------------------
async def get_storage_summary() -> Dict[str, Any]:
    pools = await list_pools_db()
    disks = await list_disks_db()
    datasets = await list_datasets_db()
    total_bytes = sum(d.get("size_bytes") or 0 for d in disks)
    return {
        "pools": pools,
        "disks": disks,
        "datasets": datasets,
        "total_bytes": total_bytes,
        "total_capacity": f"{total_bytes}"
    }



# -------------------------
# Pool operations (high-level)
# -------------------------
async def create_zfs_pool(name: str, devices: List[str], raidz: Optional[str] = None, dry_run: bool = True, force: bool = False) -> Dict[str, Any]:
    """
    If dry_run True -> return a preview of zpool create command and expected layout.
    If dry_run False -> perform zpool create and persist to DB.
    """
    # Build command preview
    cmd = ["zpool", "create", name]
    # translate raidz to vdev layout minimal:
    if raidz and raidz.startswith("raidz"):
        cmd.append(raidz)
    cmd.extend(devices)

    preview = {"cmd": cmd, "devices": devices, "raidz": raidz}

    if dry_run:
        return {"preview": preview}

    # perform creation via safe_exec
    r = await safe_exec(cmd, sudo=True, timeout=60 * 5)
    if not r.get("ok"):
        return {"ok": False, "stderr": r.get("stderr")}

    # add DB record
    pool = await create_pool_record(name, type_="zfs", properties={"raidz": raidz, "force": force})
    for idx, dev in enumerate(devices):
        await add_pool_device(pool["id"], dev, role="data", vdev_index=idx)

    # broadcast storage update
    await WSManagerProxy.broadcast({"module": "storage", "event": "summary_updated"})

    return {"ok": True, "pool": pool}


async def remove_disk_record(name_or_devpath: str) -> bool:
    """Delete a disk record manually."""
    try:
        return await remove_disk(name_or_devpath)
    except Exception as e:
        logger.exception("remove_disk_record failed: %s", e)
        return False        


#async def destroy_zfs_pool(name: str) -> Dict[str, Any]:
 #   try:
      #  ok = await zfs_manager.destroy_pool(name)
        # delete DB record
       # await db.exec("DELETE FROM pools WHERE name=%s", (name,))
        #await WSManagerProxy.broadcast({"module": "zfs", "event": "pool_destroyed", "data": {"pool": name}})
       # return {"deleted": bool(ok)}
    #except Exception as e:
     #   logger.exception("destroy_zfs_pool failed: %s", e)
      #  return {"error": str(e)}


async def destroy_zfs_pool(name: str) -> Dict[str, Any]:
    # zpool destroy
    r = await safe_exec(["zpool", "destroy", name], sudo=True, timeout=60 * 2)
    if not r.get("ok"):
        return {"ok": False, "stderr": r.get("stderr")}
    # remove db record
    await remove_pool(name)
    await WSManagerProxy.broadcast({"module": "storage", "event": "summary_updated"})
    return {"ok": True}
    

async def import_pool(name: str) -> Dict[str, Any]:
    try:
        ok = await zfs_manager.import_pool(name)
        if ok:
            # re-sync pool list from zfs_manager
            pools = await zfs_manager.list_pools()
            for p in pools:
                topo = json.dumps(p.get("topology", {}))
                await db.exec("INSERT INTO pools (name, topology_json) VALUES (%s,%s) ON DUPLICATE KEY UPDATE topology_json=%s", (p["name"], topo, topo))
            await WSManagerProxy.broadcast({"module": "zfs", "event": "pool_imported", "data": {"pool": name}})
        return {"imported": bool(ok)}
    except Exception as e:
        logger.exception("import_pool failed: %s", e)
        return {"error": str(e)}
        
async def get_storage_alerts():
    """
    Returns SMART failures, degraded pools, missing disks, etc.
    """
    alerts = []

    # SMART Alerts
    smart_rows = await raw("SELECT * FROM disk_smart WHERE status != 'OK'")
    for r in smart_rows or []:
        alerts.append({
            "type": "SMART",
            "disk": r["disk"],
            "message": f"SMART failure: {r['status']}"
        })

    # Degraded Pools
    pools = await raw("SELECT * FROM pools WHERE health != 'ONLINE'")
    for p in pools or []:
        alerts.append({
            "type": "POOL",
            "pool": p["name"],
            "message": f"Pool health = {p['health']}"
        })

    return alerts

    async def import_pool2(name: str) -> Dict[str, Any]:
     info = await zfs_manager.import_pool(name)
     if not info.get("ok"):
        return {"ok": False, "error": info.get("error")}
     pool = await _driver.create_pool_record(name, pool_type="zfs", meta=info.get("meta") or {})
     for v in info.get("vdevs", []):
        vdev = await _driver.add_vdev(pool_id=pool.id, vdev_type=v.get("type"), role=v.get("role"), meta=v.get("meta"))
        for diskname in v.get("disks", []):
            nm = diskname.split("/")[-1] if "/" in diskname else diskname
            await _driver.add_vdev_disk(vdev_id=vdev.id, disk_name=nm)
     return {"ok": True, "pool_id": pool.id}
