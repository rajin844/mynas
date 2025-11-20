# backend/rpc_handlers/zfs.py
from typing import Any, Dict, List
import logging
from backend.storage.zfs_manager import (
    list_pools,
    list_datasets,
    create_pool,
    create_dataset,
    destroy_pool,
    destroy_dataset,
)

logger = logging.getLogger("mynas.rpc.zfs")

def rpc_listpools() -> List[Dict[str, Any]]:
    return list_pools()

def rpc_listdatasets(pool: str = None) -> List[Dict[str, Any]]:
    return list_datasets(pool)

def rpc_createpool(name: str, devices: list, raidz: str = None, dry_run: bool = True) -> Dict[str, Any]:
    return create_pool(name, devices, raidz=raidz, dry_run=dry_run)

def rpc_createdataset(pool: str, name: str, mountpoint: str = None) -> Dict[str, Any]:
    ok = create_dataset(pool, name, mountpoint)
    return {"created": bool(ok)}

def rpc_destroypool(name: str) -> Dict[str, Any]:
    ok = destroy_pool(name)
    return {"deleted": bool(ok)}

def rpc_destroydataset(pool: str, name: str) -> Dict[str, Any]:
    ok = destroy_dataset(pool, name)
    return {"deleted": bool(ok)}

def register_rpc(register):
    register("zfs", {
        "listpools": rpc_listpools,
        "listdatasets": rpc_listdatasets,
        "createpool": rpc_createpool,
        "createdataset": rpc_createdataset,
        "destroypool": rpc_destroypool,
        "destroydataset": rpc_destroydataset,
    })
