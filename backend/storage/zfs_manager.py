# backend/storage/zfs_manager.py
from typing import Optional, List, Dict, Any
import logging
from backend.drivers import zfs_driver_mysql
from backend.drivers.storage_driver_mysql import (
    list_disks_db,
    get_disk_by_devpath,
    get_disk_by_name,
    list_datasets_db,
    create_pool_record,
    add_pool_device,
    create_dataset_record,
    remove_pool_record,
)
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.zfs_manager")


async def list_pools() -> List[Dict[str, Any]]:
    return await zfs_driver_mysql.zfs_list_pools()


async def list_datasets(pool: Optional[str] = None) -> List[Dict[str, Any]]:
    return await zfs_driver_mysql.zfs_list_datasets(pool)


async def create_pool(name: str, devices: List[str], raidz: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    # call storage_manager.create_zfs_pool for consistent workflow
    from backend.storage.storage_manager import create_zfs_pool
    return await create_zfs_pool(name, devices, raidz=raidz, dry_run=False, force=force)


async def preview_create_pool(name: str, devices: List[str], raidz: Optional[str] = None) -> Dict[str, Any]:
    from backend.storage.storage_manager import create_zfs_pool
    return await create_zfs_pool(name, devices, raidz=raidz, dry_run=True)


async def create_dataset(pool: str, name: str, mountpoint: Optional[str] = None) -> Dict[str, Any]:
    from backend.app.safe_exec import safe_exec
    full = f"{pool}/{name}"
    r = await safe_exec(["zfs", "create", full], sudo=True)
    if r.get("ok"):
        await create_dataset_record(pool, name, mountpoint=mountpoint)
        await WSManagerProxy.broadcast({"module": "zfs", "event": "dataset_created", "pool": pool, "dataset": name})
    return r


async def destroy_dataset(pool: str, name: str) -> Dict[str, Any]:
    from backend.app.safe_exec import safe_exec
    full = f"{pool}/{name}"
    r = await safe_exec(["zfs", "destroy", full], sudo=True)
    if r.get("ok"):
        await WSManagerProxy.broadcast({"module": "zfs", "event": "dataset_destroyed", "pool": pool, "dataset": name})
    return r


async def destroy_pool(name: str) -> bool:
    from backend.app.safe_exec import safe_exec
    r = await safe_exec(["zpool", "destroy", name], sudo=True)
    if r.get("ok"):
        # optionally remove DB record
        try:
            if hasattr(driver, "exec_remove_pool"):
                await driver.exec_remove_pool(name)
        except Exception:
            pass
        await WSManagerProxy.broadcast({"module": "zfs", "event": "pool_destroyed", "pool": name})
        return True
    return False
