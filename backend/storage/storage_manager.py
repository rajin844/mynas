# backend/storage/storage_manager.py
from typing import List, Dict, Any, Optional
import logging
import asyncio
import json
import shutil

#from backend.drivers import db
from backend.drivers.storage_driver_mysql import (
    list_disks_db,
    add_or_update_disk,
    get_disk_by_devpath,
    get_disk_by_name,
    list_datasets_db,
    create_pool_record,
    add_pool_device,
    create_dataset_record,
    remove_pool_record,
)
from backend.drivers import zfs_driver_mysql
from backend.app.safe_exec import safe_exec
from backend.storage.raidz_manager import build_raidz_layout
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.storage_manager")


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


async def list_disks() -> List[Dict[str, Any]]:
    return await list_disks_db()


async def get_storage_summary() -> Dict[str, Any]:
    """
    Return combined summary: disks, pools, datasets counts.
    """
    disks = await list_disks_db()
    pools = await list_pools_db()
    datasets = await list_datasets_all()
    # compute simple capacity metrics if available
    return {
        "disks": disks,
        "pools": pools,
        "datasets": datasets,
        "total_capacity": None,
    }


# Wraps zfs create using raidz builder & zfs driver
async def create_zfs_pool(name: str, devices: List[str], raidz: Optional[str] = None, dry_run: bool = True, force: bool = False) -> Dict[str, Any]:
    """
    devices: list of /dev/sdX or names
    raidz: 'single'|'mirror'|'raidz1'|'raidz2'|'raidz3'
    """
    # Build vdev layout
    layout = build_raidz_layout(devices, raidz or "single")
    vdevs = [v["disks"] for v in layout["vdevs"]]
    # preview via zfs_driver
    preview = await zfs_driver.zfs_create_pool(name, vdevs, raidz=raidz, force=force, dry_run=dry_run)
    if dry_run:
        return {"preview": preview, "layout": layout}
    # Execute creation
    res = await zfs_driver.zfs_create_pool(name, vdevs, raidz=raidz, force=force, dry_run=False)
    if res.get("ok"):
        # persist pool topology
        await driver.create_pool_record(name, layout)
        # broadcast event
        await WSManagerProxy.broadcast({"module": "storage", "event": "summary_updated"})
    return res


async def destroy_zfs_pool(name: str) -> Dict[str, Any]:
    from backend.app.safe_exec import safe_exec
    r = await safe_exec(["zpool", "destroy", name], sudo=True)
    if r.get("ok"):
        # Optionally remove DB record
        await remove_pool(name) if hasattr(driver, "exec_remove_pool") else None
        await WSManagerProxy.broadcast({"module": "storage", "event": "summary_updated"})
    return r


# Helper functions to list pools and datasets via zfs_driver or DB
async def list_pools() -> List[Dict[str, Any]]:
    # prefer zfs discovery then DB
    try:
        pools = await zfs_driver.zfs_list_pools()
        # persist to DB if needed
        for p in pools:
            await driver.create_pool_record(p["name"], {"health": p.get("health")})
        return pools
    except Exception:
        return await driver.list_pools_db()


async def list_datasets(pool: Optional[str] = None) -> List[Dict[str, Any]]:
    return await zfs_driver.zfs_list_datasets(pool)


async def list_datasets_all() -> List[Dict[str, Any]]:
    return await zfs_driver.zfs_list_datasets(None)
