# backend/storage/zfs_manager.py
import logging
from typing import List, Dict, Any, Optional
from backend.drivers.db import run_query
from backend.drivers.zfs_driver_mysql import list_pools_db
from backend.drivers.storage_driver_mysql import (
    list_datasets_db,
    create_pool_record,
    add_pool_device,
    create_dataset_record,
    remove_pool_record,
)
from backend.app.safe_exec import safe_exec
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.zfs")
 
async def list_pools() -> List[Dict[str, Any]]:
   return await list_pools_db()

#async def scansystem() -> List[Dict[str, Any]]:
 #  return await scan_system_pools()

async def list_datasets(pool: Optional[str] = None) -> List[Dict[str, Any]]:
    return await list_datasets_db(pool)


async def preview_create_pool(name: str, devices: List[str], raidz: Optional[str] = None) -> Dict[str, Any]:
    cmd = ["zpool", "create", name]
    if raidz:
        cmd.append(raidz)
    cmd.extend(devices)
    return {"cmd": cmd, "devices": devices, "raidz": raidz}


async def create_pool(name: str, devices: List[str], raidz: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    # run zpool create
    cmd = ["zpool", "create", name]
    if raidz:
        cmd.append(raidz)
    cmd.extend(devices)
    r = await safe_exec(cmd, sudo=True, timeout=60 * 5)
    if not r.get("ok"):
        return {"ok": False, "stderr": r.get("stderr")}

    pool = await create_pool_record(name, type_="zfs", properties={"raidz": raidz})
    for idx, dev in enumerate(devices):
        await add_pool_device(pool["id"], dev, role="data", vdev_index=idx)

    await WSManagerProxy.broadcast({"module": "zfs", "event": "pools_updated"})
    return {"ok": True, "pool": pool}


async def destroy_pool(name: str) -> Dict[str, Any]:
    r = await safe_exec(["zpool", "destroy", name], sudo=True, timeout=60 * 2)
    if not r.get("ok"):
        return {"ok": False, "stderr": r.get("stderr")}
    await remove_pool(name)
    await WSManagerProxy.broadcast({"module": "zfs", "event": "pools_updated"})
    return {"ok": True}


async def create_dataset(pool: str, name: str, mountpoint: Optional[str] = None) -> Dict[str, Any]:
    full = f"{pool}/{name}"
    r = await safe_exec(["zfs", "create", full], sudo=True, timeout=60)
    if not r.get("ok"):
        return {"ok": False, "stderr": r.get("stderr")}
    ds = await create_dataset_record(pool, name, mountpoint)
    await WSManagerProxy.broadcast({"module": "zfs", "event": "datasets_updated", "pool": pool})
    return {"ok": True, "dataset": ds}


async def destroy_dataset(pool: str, name: str) -> Dict[str, Any]:
    full = f"{pool}/{name}"
    r = await safe_exec(["zfs", "destroy", full], sudo=True, timeout=60)
    if not r.get("ok"):
        return {"ok": False, "stderr": r.get("stderr")}
    # remove dataset from DB
    await run_query("DELETE FROM datasets WHERE pool_id=(SELECT id FROM pools WHERE name=:name) AND name=:dsname", {"name": pool, "dsname": name}, fetch=False)
    await WSManagerProxy.broadcast({"module": "zfs", "event": "datasets_updated", "pool": pool})
    return {"ok": True}

async def import_pool(name: str) -> bool:
    try:
        r = await safe_exec(["zpool", "import", name], timeout=30, sudo=True)
        if not r.get("ok"):
            logger.warning("zpool import failed: %s", r.get("stderr"))
            return False
        await WSManagerProxy.broadcast({"module": "zfs", "event": "pool_imported", "data": {"name": name}})
        return True
    except Exception as e:
        logger.exception("import_pool failed: %s", e)
        return False

      #r = await safe_exec(["zfs", "list", "-H", "-o", "name,mountpoint"], sudo=True)
    #try:
     #   if pool_name:
      #      pool = await get_pool_by_name(pool_name)
       #     if not pool:
        #        return []
         #   rows = await run_query("SELECT * FROM datasets WHERE pool_id = :pid ORDER BY name ASC", {"pid": pool["id"]})
          #  if rows:
           #     return [
            #        {
             #           "pool_name": pool_name,
              #          "name": r["name"],
               #         "mountpoint": r["mountpoint"],
                #    }
                 #   for r in rows
                #]
            #return rows
        #else:
         ##      "SELECT d.*, p.name as pool_name FROM datasets d JOIN pools p ON d.pool_id = p.id ORDER BY p.name, d.name",
           #     {},
            # )
           # return rows
    # except Exception as e:
    #    logger.exception("list_datasets_db failed: %s", e)
     #   return []
    
   # try:
    #    if pool_name:
     #       pool = await get_pool_by_name(pool_name)
      #      if not pool:
       #        return []
        #    rows = await run_query("SELECT * FROM datasets WHERE pool_id = :pid ORDER BY name ASC", {"pid": pool["id"]})
         #   for r in rows:
          #      r["pool_name"] = pool_name
            #return rows
       # else:
        #    rows = await run_query(
         #       "SELECT d.*, p.name as pool_name FROM datasets d JOIN pools p ON d.pool_id = p.id ORDER BY p.name, d.name",
          #      {},
           # )
            #return rows
   # except Exception as e:
    #    logger.exception("list_datasets_db failed: %s", e)
     #   return []    


