# backend/drivers/storage_driver_mysql.py
"""
MySQL-backed Storage Driver.

Implements the StorageDriverProtocol using backend.app.db (async aiomysql pool).
This file assumes backend/app/db.py exposes run_query, run_execute, run_insert.
"""

import logging
from typing import Any, Dict, List, Optional
from backend.drivers import db

logger = logging.getLogger("mynas.storage_driver_mysql")


class StorageDriver:
    """
    MySQL-backed storage driver.

    Tables assumed (create via migrations):
      - disks (id, name, devpath, model, vendor, size_bytes, rotational, mountpoint, created_at)
      - pools (id, name, type, devices_json, properties_json, created_at)
      - datasets (id, pool, name, mountpoint, properties_json, created_at)
      - smart_history (id, disk_name, raw_json, status, temp_c, ts)
      - alerts (id, level, source, message, ts)
    """

    def __init__(self):
        # no stateful connection; db module manages the pool
        pass

    # ------------------------
    # Disks
    # ------------------------
    async def list_disks_db(self) -> List[Dict[str, Any]]:
        rows = await db.run_query("SELECT * FROM disks ORDER BY name ASC")
        return rows

    
    async def save_disk(self, disk: Dict[str, Any]):
        q = "INSERT INTO disks (name, devpath, size_bytes, model, vendor, rotational) VALUES (%s,%s,%s,%s,%s,%s)"
        await run_query(q, (disk.get("name"), disk.get("devpath"), disk.get("size_bytes"), disk.get("model"), disk.get("vendor"), disk.get("rotational")), fetch="none")
        return True

    async def save_disk_record(self, disk: Dict[str, Any]) -> int:
        """
        Upsert disk record by name or devpath.
        disk: {name, devpath, size_bytes, model, vendor, rotational, mountpoint}
        """
        # Try update first
        params = {
            "name": disk.get("name"),
            "devpath": disk.get("devpath"),
            "model": disk.get("model"),
            "vendor": disk.get("vendor"),
            "size_bytes": disk.get("size_bytes") or disk.get("size"),
            "rotational": 1 if disk.get("rotational") else 0,
            "mountpoint": disk.get("mountpoint"),
        }

        # update if exists
        q_update = """
        UPDATE disks SET
          devpath=%(devpath)s, model=%(model)s, vendor=%(vendor)s,
          size_bytes=%(size_bytes)s, rotational=%(rotational)s, mountpoint=%(mountpoint)s
        WHERE name=%(name)s
        """
        updated = await db.run_execute(q_update, params)
        if updated and updated > 0:
            return updated

        # insert
        q_insert = """
        INSERT INTO disks (name, devpath, model, vendor, size_bytes, rotational, mountpoint)
        VALUES (%(name)s, %(devpath)s, %(model)s, %(vendor)s, %(size_bytes)s, %(rotational)s, %(mountpoint)s)
        """
        lastid = await db.run_insert(q_insert, params)
        return lastid

    # ------------------------
    # Pools
    # ------------------------
    async def list_pools_db(self) -> List[Dict[str, Any]]:
        rows = await db.run_query("SELECT * FROM pools ORDER BY name")
        # parse JSON fields if needed by caller (they expect dicts)
        for r in rows:
            if "devices_json" in r and r["devices_json"]:
                try:
                    import json
                    r["devices"] = json.loads(r["devices_json"])
                except Exception:
                    r["devices"] = []
        return rows

    async def create_pool_record(self, pool: Dict[str, Any]) -> int:
        """
        pool: {name, type, devices: [...], properties: {...}}
        """
        import json
        params = {
            "name": pool.get("name"),
            "type": pool.get("type", "zfs"),
            "devices_json": json.dumps(pool.get("devices", [])),
            "properties_json": json.dumps(pool.get("properties", {})),
        }
        # upsert logic: delete existing then insert (simple)
        await db.run_execute("DELETE FROM pools WHERE name=%(name)s", {"name": params["name"]})
        q = """
        INSERT INTO pools (name, type, devices_json, properties_json)
        VALUES (%(name)s, %(type)s, %(devices_json)s, %(properties_json)s)
        """
        return await db.run_insert(q, params)

    async def remove_pool_record(self, pool_name: str) -> int:
        return await db.run_execute("DELETE FROM pools WHERE name=%(name)s", {"name": pool_name})

    # ------------------------
    # Datasets
    # ------------------------
    async def list_datasets_db(self, pool: Optional[str] = None) -> List[Dict[str, Any]]:
        if pool:
            return await db.run_query("SELECT * FROM datasets WHERE pool=%(pool)s ORDER BY name", {"pool": pool})
        return await db.run_query("SELECT * FROM datasets ORDER BY pool, name")

    async def create_dataset_record(self, pool: str, name: str, mountpoint: Optional[str] = None) -> int:
        params = {"pool": pool, "name": name, "mountpoint": mountpoint}
        # delete if exists
        await db.run_execute("DELETE FROM datasets WHERE pool=%(pool)s AND name=%(name)s", params)
        q = "INSERT INTO datasets (pool, name, mountpoint) VALUES (%(pool)s, %(name)s, %(mountpoint)s)"
        return await db.run_insert(q, params)

    async def delete_dataset_record(self, pool: str, name: str) -> int:
        return await db.run_execute("DELETE FROM datasets WHERE pool=%(pool)s AND name=%(name)s", {"pool": pool, "name": name})

    # ------------------------
    # SMART / Alerts
    # ------------------------
    async def add_smart_history(self, disk_name: str, raw: Dict[str, Any], status: str, temp_c: Optional[float]) -> int:
        import json, time
        params = {
            "disk_name": disk_name,
            "raw_json": json.dumps(raw),
            "status": status,
            "temp_c": temp_c,
            "ts": int(time.time())
        }
        q = """
        INSERT INTO smart_history (disk_name, raw_json, status, temp_c, ts)
        VALUES (%(disk_name)s, %(raw_json)s, %(status)s, %(temp_c)s, FROM_UNIXTIME(%(ts)s))
        """
        return await db.run_insert(q, params)

    async def push_alert(self, level: str, source: str, message: str) -> int:
        import time
        params = {"level": level, "source": source, "message": message, "ts": int(time.time())}
        q = "INSERT INTO alerts (level, source, message, ts) VALUES (%(level)s, %(source)s, %(message)s, FROM_UNIXTIME(%(ts)s))"
        return await db.run_insert(q, params)

    # ------------------------
    # Misc helpers
    # ------------------------
    async def get_pool_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        r = await db.run_query("SELECT * FROM pools WHERE name=%(name)s", {"name": name})
        return r[0] if r else None
