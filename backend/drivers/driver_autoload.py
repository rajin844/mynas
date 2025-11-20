# backend/app/driver_autoload.py
from backend.app.drivers.zfs_driver import ZFSStorageDriver
from backend.app.drivers.ext4_driver import EXT4StorageDriver
from backend.app.drivers.btrfs_driver import BTRFSStorageDriver
from backend.app.drivers.cloud_driver import CloudStorageDriver
from backend.app.driver_persistence import driverdb

def get_driver_for(pool_type: str):
    pool_type = pool_type.lower()

    if pool_type == "zfs":
        return ZFSStorageDriver()
    if pool_type == "ext4":
        return EXT4StorageDriver()
    if pool_type == "btrfs":
        return BTRFSStorageDriver()
    if pool_type == "cloud":
        return CloudStorageDriver()

    raise ValueError(f"Unknown storage backend: {pool_type}")

def autodetect_and_get(pool_name: str):
    meta = driverdb.get_pool(pool_name)
    if not meta:
        raise ValueError(f"No metadata found for pool '{pool_name}'")

    return get_driver_for(meta["type"])
