# backend/storage/zfs_manager.py
import logging
import json
from typing import List, Dict, Any, Optional
from backend.drivers.db import run_query ,fetch_one
from backend.app.safe_exec import safe_exec
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.zfs")

# -----------------
# List pools
# -----------------
async def list_pools() -> List[Dict[str, Any]]:
    """Return pools from DB; if empty probe zpool list."""
    rows = await run_query("SELECT id, name, type, health, devices, created_at FROM pools ORDER BY id DESC", {})
    if rows:
        return [dict(r) for r in rows]

    # fallback: probe zpool
    r = await safe_exec(["zpool", "list", "-H", "-o", "name,health,size,alloc,free,cap"], timeout=8, sudo=True)
    if r.get("ok"):
        lines = r["stdout"].splitlines()
        pools = []
        for line in lines:
            parts = line.split()
            name = parts[0]
            health = parts[1] if len(parts) > 1 else "UNKNOWN"
            pools.append({"name": name, "health": health})
            # upsert into DB
            await run_query(
    """
    INSERT INTO pools (name, type, health, devices_json, created_at)
    VALUES (:name, 'zfs', :health, :devices, NOW()) AS _new
    ON DUPLICATE KEY UPDATE
      health = _new.health,
      devices_json = _new.devices_json
    """,
    {"name": name, "health": health, "devices": "[]"}
)
        return pools
    return []

# -----------------
# Datasets
# -----------------

async def get_pool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a pool by name.
    Adds 'pool_name' key because callers expect it.
    """
    try:
        rows = await run_query(
            """
            SELECT *
            FROM pools
            WHERE name = :name
            LIMIT 1
            """,
            {"name": name}
        )

        if not rows:
            return None

        pool = rows[0]

        # callers expect pool_name even though DB column is 'name'
        pool["pool_name"] = pool["name"]

        return pool

    except Exception as e:
        logger.exception(f"get_pool_by_name() failed: {e}")
        return None

def parse_human_size(val: str) -> int:
    """
    Convert ZFS human sizes like:
      5G, 320M, 1024K, 12T, 500B
    into bytes (int).
    """
    if not val:
        return 0

    val = val.strip().upper()

    units = {
        "B": 1,
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
        "T": 1024**4,
        "P": 1024**5
    }

    # Example: "5G" → num = 5, unit = G
    num = ''
    unit = ''

    for ch in val:
        if ch.isdigit() or ch == '.':
            num += ch
        else:
            unit += ch

    if not num:
        return 0

    mult = units.get(unit, 1)

    return int(float(num) * mult)

async def list_datasets(pool_name: Optional[str] = None) -> List[Dict[str, Any]]:
   # 1) Try DB
    rows = await run_query(
        "SELECT id, pool, name, mountpoint, used_bytes, available_bytes, created_at FROM datasets ORDER BY id DESC"
     )
    if rows:
        return rows

    # 2) Fallback → ZFS probe
    r = await safe_exec(
        ["zfs", "list", "-H", "-o", "name,used,available,mountpoint"],
        timeout=8,
        sudo=True
    )

    if not r.get("ok"):
        return []

    datasets = []

    pool_rows = await run_query("SELECT id, name FROM pools")
    pool_map = {row["name"]: row["id"] for row in pool_rows}

    for line in r["stdout"].splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue

        name = parts[0]
        used = parts[1]
        available = parts[2]
        mount = parts[3]

        

        pool = name.split("/")[0]
        pool_id = pool_map.get(pool)


        used_b = parse_human_size(used)
        avail_b = parse_human_size(available)

        datasets.append({
            "name": name,
            "pool": pool,
            "pool_id": pool_id,
            "mountpoint": mount,
            "used_bytes": used_b,
            "available_bytes": avail_b
        })
    
        # UPSERT (MySQL 8+)
        await run_query("""
            INSERT INTO datasets(name, pool, pool_id, mountpoint, used_bytes, available_bytes)
             VALUES(:name, :pool, :pool_id, :mountpoint, :used_bytes, :available_bytes) AS new
          ON DUPLICATE KEY UPDATE
                mountpoint = new.mountpoint,
                used_bytes = new.used_bytes,
                available_bytes = new.available_bytes
          """, {
            "name": name,
            "pool": pool,
            "pool_id": pool_id,
            "mountpoint": mount,
            "used_bytes": used_b,
            "available_bytes": avail_b 
            }
        )
 
    return datasets


# -----------------
# Create / destroy dataset
# -----------------

async def create_dataset(pool: str, name: str, mountpoint: Optional[str] = None) -> Dict[str, Any]:
    full = f"{pool}/{name}"
    r = await safe_exec(["zfs", "create", full], timeout=20, sudo=True)
    if not r.get("ok"):
        raise RuntimeError(r.get("stderr"))
    await run_query("INSERT INTO datasets (pool, name, mountpoint, created_at) VALUES (:pool, :name, :mp, NOW())", {"pool": pool, "name": name, "mp": mountpoint})
    await WSManagerProxy.broadcast({"module": "zfs", "event": "dataset_created", "dataset": full})
    return {"ok": True, "name": full}

async def destroy_dataset(pool: str, name: str) -> Dict[str, Any]:
    full = f"{pool}/{name}"
    r = await safe_exec(["zfs", "destroy", full], timeout=20, sudo=True)
    if not r.get("ok"):
        raise RuntimeError(r.get("stderr"))
    await run_query("DELETE FROM datasets WHERE pool=:pool AND name=:name", {"pool": pool, "name": name})
    await WSManagerProxy.broadcast({"module": "zfs", "event": "dataset_destroyed", "dataset": full})
    return {"ok": True}
