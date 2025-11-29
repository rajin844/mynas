# backend/storage/storage_driver_mysql.py
"""
MySQL-backed Storage Driver for MyNAS
Uses backend.app.db.run_query / fetch_one

Provides:
 - Disks: list, get, add_or_update, remove, sync
 - Pools: list, get_by_name, create, remove
 - Pool devices (vdevs): add, list
 - Datasets: list, get, create, remove

All functions are async and return JSON-serializable dicts/lists.
"""

from typing import List, Dict, Any, Optional
import json
import logging

from backend.drivers.db import run_query, fetch_one

logger = logging.getLogger("mynas.storage.driver")


# -------------------------
# Disks
# -------------------------
async def list_disks_db() -> List[Dict[str, Any]]:
    """Return all disks from DB."""
    try:
        rows = await run_query(
           # "SELECT id, name, devpath, model, vendor, size_bytes, rotational, mountpoint, last_seen FROM disks ORDER BY name",
            "SELECT id, name, devpath, model, vendor, size_bytes, rotational, mountpoint, last_seen FROM disks ORDER BY name",
            {},
            fetch=True,
        )
        return rows
    except Exception as e:
        logger.exception("list_disks_db failed: %s", e)
        return []


async def get_disk_by_devpath(devpath: str) -> Optional[Dict[str, Any]]:
    """Return single disk by devpath."""
    try:
        return await fetch_one("SELECT * FROM disks WHERE devpath = :dev LIMIT 1", {"dev": devpath})
    except Exception as e:
        logger.exception("get_disk_by_devpath failed: %s", e)
        return None


async def get_disk_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Return single disk by name (e.g. sda)."""
    try:
        return await fetch_one("SELECT * FROM disks WHERE name = :name LIMIT 1", {"name": name})
    except Exception as e:
        logger.exception("get_disk_by_name failed: %s", e)
        return None


async def add_or_update_disk(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert or update a disk record.
    rec keys expected: name, devpath, model, vendor, size_bytes, rotational, mountpoint(optional)
    Returns the DB record for the disk.
    """
    try:
        name = rec.get("name")
        devpath = rec.get("devpath")
        model = rec.get("model") or None
        vendor = rec.get("vendor") or None
        size_bytes = int(rec.get("size_bytes") or 0)
        rotational = 1 if rec.get("rotational") else 0
        mountpoint = rec.get("mountpoint")

        if not name or not devpath:
            logger.warning("add_or_update_disk missing name/devpath: %s", rec)
            return {}

        # Check existing by devpath first, then name
        existing = await get_disk_by_devpath(devpath)
        if not existing:
            existing = await get_disk_by_name(name)

        if existing:
            # update
            await run_query(
                """
                UPDATE disks
                SET name = :name,
                    devpath = :dev,
                    model = :model,
                    vendor = :vendor,
                    size_bytes = :size,
                    rotational = :rot,
                    mountpoint = :mnt,
                    last_seen = NOW()
                WHERE id = :id
                """,
                {
                    "name": name,
                    "dev": devpath,
                    "model": model,
                    "vendor": vendor,
                    "size": size_bytes,
                    "rot": rotational,
                    "mnt": mountpoint,
                    "id": existing["id"],
                },
                fetch=False,
            )
            return await fetch_one("SELECT * FROM disks WHERE id = :id", {"id": existing["id"]})
        else:
            # insert
            await run_query(
                """
                INSERT INTO disks (name, devpath, model, vendor, size_bytes, rotational, mountpoint, last_seen)
                VALUES (:name, :dev, :model, :vendor, :size, :rot, :mnt, NOW())
                """,
                {
                    "name": name,
                    "dev": devpath,
                    "model": model,
                    "vendor": vendor,
                    "size": size_bytes,
                    "rot": rotational,
                    "mnt": mountpoint,
                },
                fetch=False,
            )
            return await get_disk_by_devpath(devpath)

    except Exception as e:
        logger.exception("add_or_update_disk failed: %s | rec=%s", e, rec)
        return {}


async def remove_disk(name_or_devpath: str) -> bool:
    """Remove disk by name or devpath. Returns True if any row affected."""
    try:
        # try by devpath
        res = await run_query("DELETE FROM disks WHERE devpath = :v OR name = :v", {"v": name_or_devpath}, fetch=False)
        return bool(res and res.get("rows_affected"))
    except Exception as e:
        logger.exception("remove_disk failed: %s", e)
        return False


async def remove_pool(name: str) -> Dict[str, Any]:
    pool = await get_pool_by_name(name)
    if not pool:
        return {"deleted": False}
    await run_query("DELETE FROM pools WHERE id=:id", {"id": pool["id"]}, fetch=False)
    return {"deleted": True}

async def sync_disks_db(disks: List[Dict[str, Any]]) -> None:
    """
    Replace disk table with provided list.
    Each disk should be a dict containing name, devpath, model, vendor, size_bytes, rotational, mountpoint(optional)
    """
    try:
        # Simple approach: truncate then insert (safe for discovered disks)
        await run_query("DELETE FROM disks", {}, fetch=False)
        for d in disks:
            await add_or_update_disk(d)
    except Exception as e:
        logger.exception("sync_disks_db failed: %s", e)
        raise


# -------------------------
# Pools
# -------------------------
async def list_pools_db() -> List[Dict[str, Any]]:
    pools = await run_query("SELECT * FROM pools ORDER BY id DESC", {})
    out = []
    for p in pools:
        devs = await run_query("SELECT devpath, role, vdev_index FROM pool_devices WHERE pool_id=:pid", {"pid": p["id"]})
        out.append({**p, "devices": [d for d in devs]})
    return out

async def get_pool_by_name(name: str) -> Optional[Dict[str, Any]]:
    try:
        return await fetch_one("SELECT * FROM pools WHERE name = :name LIMIT 1", {"name": name})
    except Exception as e:
        logger.exception("get_pool_by_name failed: %s", e)
        return None


async def create_pool_record(name: str, type_: str = "zfs", properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create pool metadata DB record. Returns created pool row.
    """
    try:
        props_json = json.dumps(properties or {})
        await run_query(
            "INSERT INTO pools (name, type, properties, health, created_at) VALUES (:name, :type, :props, :health, NOW())",
            {"name": name, "type": type_, "props": props_json, "health": "ONLINE"},
            fetch=False,
        )
        return await get_pool_by_name(name)
    except Exception as e:
        logger.exception("create_pool_record failed: %s", e)
        return {}


async def remove_pool_record(name: str) -> bool:
    """Delete pool and its devices via FK cascade. Returns True if deleted."""
    try:
        pool = await get_pool_by_name(name)
        if not pool:
            return False
        res = await run_query("DELETE FROM pools WHERE id = :id", {"id": pool["id"]}, fetch=False)
        return bool(res and res.get("rows_affected"))
    except Exception as e:
        logger.exception("remove_pool_record failed: %s", e)
        return False


# -------------------------
# Pool devices (vdevs)
# -------------------------
async def add_pool_device(pool_id: int, devpath: str, role: str = "data", vdev_index: int = 0) -> None:
    try:
        await run_query(
            "INSERT INTO pool_devices (pool_id, devpath, role, vdev_index) VALUES (:pid, :dev, :role, :vidx)",
            {"pid": pool_id, "dev": devpath, "role": role, "vidx": vdev_index},
            fetch=False,
        )
    except Exception as e:
        logger.exception("add_pool_device failed: %s", e)
        raise


async def list_pool_devices(pool_id: int) -> List[Dict[str, Any]]:
    try:
        return await run_query(
            "SELECT id, devpath, role, vdev_index FROM pool_devices WHERE pool_id = :pid ORDER BY vdev_index ASC",
            {"pid": pool_id},
        )
    except Exception as e:
        logger.exception("list_pool_devices failed: %s", e)
        return []


async def remove_pool_device(pool_id: int, devpath: str) -> bool:
    try:
        res = await run_query(
            "DELETE FROM pool_devices WHERE pool_id = :pid AND devpath = :dev",
            {"pid": pool_id, "dev": devpath},
            fetch=False,
        )
        return bool(res and res.get("rows_affected"))
    except Exception as e:
        logger.exception("remove_pool_device failed: %s", e)
        return False


# -------------------------
# Datasets
# -------------------------
async def list_datasets_db(pool_name: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        if pool_name:
            pool = await get_pool_by_name(pool_name)
            if not pool:
                return []
            rows = await run_query("SELECT * FROM datasets WHERE pool_id = :pid ORDER BY name ASC", {"pid": pool["id"]})
            for r in rows:
                r["pool_name"] = pool_name
            return rows
        else:
            rows = await run_query(
                "SELECT d.*, p.name as pool_name FROM datasets d JOIN pools p ON d.pool_id = p.id ORDER BY p.name, d.name",
                {},
            )
            return rows
    except Exception as e:
        logger.exception("list_datasets_db failed: %s", e)
        return []


async def get_dataset_db(pool_name: str, ds_name: str) -> Optional[Dict[str, Any]]:
    try:
        pool = await get_pool_by_name(pool_name)
        if not pool:
            return None
        return await fetch_one("SELECT * FROM datasets WHERE pool_id = :pid AND name = :name LIMIT 1", {"pid": pool["id"], "name": ds_name})
    except Exception as e:
        logger.exception("get_dataset_db failed: %s", e)
        return None


async def create_dataset_record(pool_name: str, name: str, mountpoint: Optional[str] = None, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        pool = await get_pool_by_name(pool_name)
        if not pool:
            raise RuntimeError("Pool not found")
        props = json.dumps(properties or {})
        await run_query(
            "INSERT INTO datasets (pool_id, name, mountpoint, properties, created_at) VALUES (:pid, :name, :mount, :props, NOW())",
            {"pid": pool["id"], "name": name, "mount": mountpoint, "props": props},
            fetch=False,
        )
        return await get_dataset_db(pool_name, name)
    except Exception as e:
        logger.exception("create_dataset_record failed: %s", e)
        return {}


async def remove_dataset_record(pool_name: str, name: str) -> bool:
    try:
        pool = await get_pool_by_name(pool_name)
        if not pool:
            return False
        res = await run_query(
            "DELETE FROM datasets WHERE pool_id = :pid AND name = :name",
            {"pid": pool["id"], "name": name},
            fetch=False,
        )
        return bool(res and res.get("rows_affected"))
    except Exception as e:
        logger.exception("remove_dataset_record failed: %s", e)
        return False


