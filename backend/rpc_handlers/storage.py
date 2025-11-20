# backend/rpc_handlers/storage.py
from typing import Any, Dict
from backend.app.driver_persistence import driverdb
from backend.storage.storage_manager import create_pool, list_pools, destroy_pool, list_datasets
from backend.storage.raidz_manager import build_layout

# backend/rpc_handlers/storage.py --- new file code
from typing import Any, Dict
from backend.storage.raidz_manager import build_layout
from backend.app.driver_persistence import driverdb
from backend.app.drivers.zfs_driver import ZFSStorageDriver
from backend.app.drivers.ext4_driver import EXT4StorageDriver

def rpc_preview_pool(pool_type: str, disks: list, raid: str = "single", mirrors:int=2, vdevs:int=1):
    # return preview: for zfs use raidz manager, for ext4/btrfs basic mapping
    if pool_type == "zfs":
        return build_layout(raid, disks, mirrors=mirrors, vdevs=vdevs)
    else:
        return {"vdevs": [{"type": pool_type, "disks": disks}]}

def rpc_create_pool(name: str, devices: list, pool_type: str = "zfs", raidz: str = None, dry_run: bool = True):
    # delegate to API driver flow (or call driver directly)
    from backend.app.drivers.zfs_driver import ZFSStorageDriver
    from backend.app.drivers.ext4_driver import EXT4StorageDriver
    from backend.app.drivers.btrfs_driver import BTRFSStorageDriver

    if pool_type == "zfs":
        drv = ZFSStorageDriver()
    elif pool_type == "ext4":
        drv = EXT4StorageDriver()
    elif pool_type == "btrfs":
        drv = BTRFSStorageDriver()
    else:
        raise Exception("unsupported")

    return drv.create_pool(name, devices, raidz=raidz, dry_run=dry_run)


def rpc_create_pool(name: str, layout: dict, dry_run: bool=True):
    return create_pool(name, layout, dry_run=dry_run)

def rpc_list_pools():
    return list_pools()

def rpc_destroy_pool(name: str, force: bool=False):
    return destroy_pool(name, force=force)    
    
def register_rpc(register):
    register("storage", {
        "create_pool" : rpc_create_pool,
        "preview_pool": rpc_preview_pool,
        "create_pool": rpc_create_pool,
    })
