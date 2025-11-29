# backend/storage/zfs_driver_mysql.py
"""
MySQL-backed ZFS driver.

Provides DB CRUD + sync helpers for:
 - pools
 - pool_devices (vdevs)
 - datasets

Relies on:
 - backend.app.db.run_query(sql, params, fetch=True)
 - backend.app.db.fetch_one(sql, params)

Make sure DATABASE_URL and DB schema are created (see migrations/0001_initial.sql)
"""

from typing import List, Dict, Any, Optional
import json
import logging
from backend.app.safe_exec import safe_exec
from backend.drivers.db import run_query, fetch_one

logger = logging.getLogger("mynas.zfs.db")


# -------------------------
# Pools
# -------------------------

async def list_pools_db() -> List[Dict[str, Any]]:
    """
  #  Return all pools with their devices embedded.
   # """
    pools = await run_query("SELECT * FROM pools ORDER BY id DESC", {})
    out: List[Dict[str, Any]] = []
    for p in pools:
        devices = await run_query(
            "SELECT id, devpath, role, vdev_index FROM pool_devices WHERE pool_id=:pid ORDER BY vdev_index ASC",
           {"pid": p["id"]},
        )
        p_copy = dict(p)
        p_copy["devices"] = devices
        out.append(p_copy)
    return out




async def get_pool_by_name_db(name: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM pools WHERE name=:name", {"name": name})


async def create_pool_record_db(name: str, type_: str = "zfs", properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    props = json.dumps(properties or {})
    await run_query(
        "INSERT INTO pools (name, type, properties, health) VALUES (:name, :type, :props, :health)",
        {"name": name, "type": type_, "props": props, "health": "ONLINE"},
        fetch=False,
    )
    return await get_pool_by_name_db(name)


async def update_pool_properties_db(pool_id: int, properties: Dict[str, Any]):
    props = json.dumps(properties)
    await run_query(
        "UPDATE pools SET properties=:props WHERE id=:id",
        {"props": props, "id": pool_id},
        fetch=False,
    )


async def remove_pool_record_db(name: str) -> bool:
    pool = await get_pool_by_name_db(name)
    if not pool:
        return False
    await run_query("DELETE FROM pools WHERE id=:id", {"id": pool["id"]}, fetch=False)
    return True


# -------------------------
# Pool devices (vdevs)
# -------------------------
async def add_pool_device_db(pool_id: int, devpath: str, role: str = "data", vdev_index: int = 0) -> None:
    await run_query(
        "INSERT INTO pool_devices (pool_id, devpath, role, vdev_index) VALUES (:pid, :dev, :role, :vidx)",
        {"pid": pool_id, "dev": devpath, "role": role, "vidx": vdev_index},
        fetch=False,
    )


async def list_pool_devices_db(pool_id: int) -> List[Dict[str, Any]]:
    return await run_query(
        "SELECT id, devpath, role, vdev_index FROM pool_devices WHERE pool_id=:pid ORDER BY vdev_index ASC",
        {"pid": pool_id},
    )


async def remove_pool_device_db(pool_id: int, devpath: str) -> bool:
    res = await run_query(
        "DELETE FROM pool_devices WHERE pool_id=:pid AND devpath=:dev",
        {"pid": pool_id, "dev": devpath},
        fetch=False,
    )
    # run_query with fetch=False returns {"rows_affected": N} in our helper
    return bool(res and res.get("rows_affected"))


# -------------------------
# Datasets
# -------------------------
async def list_datasets_db(pool_name: Optional[str] = None) -> List[Dict[str, Any]]:
    if pool_name:
        pool = await get_pool_by_name_db(pool_name)
        if not pool:
            return []
        rows = await run_query("SELECT * FROM datasets WHERE pool_id=:pid ORDER BY name ASC", {"pid": pool["id"]})
        # attach pool name
        for r in rows:
            r["pool_name"] = pool_name
        return rows
    else:
        rows = await run_query(
            "SELECT d.*, p.name as pool_name FROM datasets d JOIN pools p ON d.pool_id = p.id ORDER BY p.name, d.name",
            {},
        )
        return rows


async def get_dataset_db(pool_name: str, ds_name: str) -> Optional[Dict[str, Any]]:
    pool = await get_pool_by_name_db(pool_name)
    if not pool:
        return None
    return await fetch_one("SELECT * FROM datasets WHERE pool_id=:pid AND name=:name", {"pid": pool["id"], "name": ds_name})


async def create_dataset_record_db(pool_name: str, name: str, mountpoint: Optional[str] = None, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    pool = await get_pool_by_name_db(pool_name)
    if not pool:
        raise RuntimeError("Pool not found")
    props = json.dumps(properties or {})
    await run_query(
        "INSERT INTO datasets (pool_id, name, mountpoint, properties) VALUES (:pid, :name, :mount, :props)",
        {"pid": pool["id"], "name": name, "mount": mountpoint, "props": props},
        fetch=False,
    )
    return await get_dataset_db(pool_name, name)


async def remove_dataset_record_db(pool_name: str, name: str) -> bool:
    pool = await get_pool_by_name_db(pool_name)
    if not pool:
        return False
    res = await run_query(
        "DELETE FROM datasets WHERE pool_id=:pid AND name=:name",
        {"pid": pool["id"], "name": name},
        fetch=False,
    )
    return bool(res and res.get("rows_affected"))


# -------------------------
# Sync helpers (used by managers)
# -------------------------
async def sync_pools_db(pools: List[Dict[str, Any]]) -> None:
    """
    Overwrite pools table with the provided pool list.
    Each pool dict may contain: name, type, properties (dict), health.
    This wipes existing pool rows and re-inserts — keep FK cascade in mind.
    """
    # Truncate or delete safely
    await run_query("DELETE FROM pool_devices", {}, fetch=False)
    await run_query("DELETE FROM pools", {}, fetch=False)

    for p in pools:
        props = json.dumps(p.get("properties") or {})
        await run_query(
            "INSERT INTO pools (name, type, properties, health) VALUES (:name, :type, :props, :health)",
            {"name": p.get("name"), "type": p.get("type", "zfs"), "props": props, "health": p.get("health", "UNKNOWN")},
            fetch=False,
        )
        pool_row = await get_pool_by_name_db(p.get("name"))
        # insert devices if provided
        for idx, d in enumerate(p.get("devices") or []):
            await add_pool_device_db(pool_row["id"], d.get("devpath") if isinstance(d, dict) else d, d.get("role") if isinstance(d, dict) else "data", idx)


async def sync_datasets_db(datasets: List[Dict[str, Any]]) -> None:
    """
    Overwrite datasets table with provided dataset list.
    Each dataset dict expected: pool (name) OR pool_id, name, mountpoint, properties
    """
    await run_query("DELETE FROM datasets", {}, fetch=False)
    for d in datasets:
        pool_name = d.get("pool") or d.get("pool_name")
        pool = await get_pool_by_name_db(pool_name)
        if not pool:
            # skip datasets for unknown pool
            logger.debug("Skipping dataset for missing pool %s", pool_name)
            continue
        props = json.dumps(d.get("properties") or {})
        await run_query(
            "INSERT INTO datasets (pool_id, name, mountpoint, properties) VALUES (:pid, :name, :mount, :props)",
            {"pid": pool["id"], "name": d.get("name"), "mount": d.get("mountpoint"), "props": props},
            fetch=False,
        )


# -------------------------
# Misc helpers
# -------------------------
async def refresh_zfs_state_db() -> None:
    """
    Optional: a hook that managers can call after import/create to refresh DB view.
    Implementations could call zpool/zfs commands, parse, and call sync_* functions.
    Here we keep it as a no-op stub for managers to implement custom behaviour.
    """
    # This is intentionally left as a stub. Managers that have system-level access
    # should call zpool/zfs and then call sync_pools_db / sync_datasets_db with parsed data.
    logger.debug("refresh_zfs_state_db called (stub)")


# -------------------------
# Utility: represent a pool/device/dataset as JSON-friendly dict
# -------------------------
def pool_row_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    # parse properties JSON string to dict if present
    try:
        out["properties"] = json.loads(row.get("properties")) if row.get("properties") else {}
    except Exception:
        out["properties"] = {}
    return out

async def scan_system_pools():
    """Scan actual ZFS pools from OS and sync to MySQL."""
    r = await safe_exec(["zpool", "list", "-Hp"], timeout=10)

    if not r["ok"]:
        logger.warning("zpool list failed: %s", r["stderr"])
        return []

    pools = []
    for line in r["stdout"].splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue

        name = parts[0]
        size = int(parts[1])
        capacity_pct = float(parts[2].replace("%", ""))

        # check if exists in DB
        db_pool = await get_pool_by_name(name)
        if not db_pool:
            await create_pool_record(name, total_size_bytes=size)
            logger.info(f"[ZFS] Inserted new pool → {name}")

        else:
            # update health/capacity
            from backend.storage.drivers.zfs_driver_mysql import update_pool_health
            await update_pool_health(name, "ONLINE", capacity_pct, size)

        pools.append(name)

    return pools

    async def zfs_list_pools() -> List[Dict[str, Any]]:
     r = await safe_exec(["zpool", "list", "-H", "-o", "name,health,capacity"], timeout=10)
     if not r.get("ok"):
        return []
     out = []
     for line in r["stdout"].splitlines():
        parts = line.split()
        if not parts:
            continue
        # naive parsing: name health capacity
        name = parts[0]
        health = parts[1] if len(parts) > 1 else "UNKNOWN"
        capacity = parts[2] if len(parts) > 2 else "0%"
        out.append({"name": name, "health": health, "used_pct": capacity.replace("%","")})
     return out


async def zfs_list_datasets(pool: Optional[str] = None) -> List[Dict[str, Any]]:
    cmd = ["zfs", "list", "-H", "-o", "name,mountpoint"]
    if pool:
        cmd = ["zfs", "list", "-H", "-o", "name,mountpoint", "-r", pool]
    r = await safe_exec(cmd, timeout=10)
    if not r.get("ok"):
        return []
    out = []
    for line in r["stdout"].splitlines():
        if not line.strip():
            continue
        name, mount = (line.split("\t") + [None])[:2]
        out.append({"name": name, "mountpoint": mount})
    return out


async def zfs_create_pool(name: str, vdevs: List[List[str]], raidz: Optional[str] = None, force: bool = False, dry_run: bool = True) -> Dict[str, Any]:
    """
    vdevs: list of vdev lists, e.g. [['/dev/sda'], ['/dev/sdb']]
    If dry_run True -> return preview (args) not execute
    """
    cmd = ["zpool", "create"]
    if force:
        cmd.append("-f")
    cmd.append(name)
    # flatten vdevs for command; supports mirror raidz etc should be built by raidz manager
    for v in vdevs:
        cmd.extend(v)
    if dry_run:
        return {"ok": True, "cmd": " ".join(cmd), "preview_vdevs": vdevs}
    r = await safe_exec(cmd, timeout=60, sudo=True)
    return r

    