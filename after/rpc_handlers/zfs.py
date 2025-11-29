# backend/rpc_handlers/zfs.py
"""
RPC handlers for zfs service (async-aware)
Registered names: "zfs"
Methods:
  - listPools
  - listDatasets
  - createPool (dry-run support)
  - destroyPool
"""

import logging
from backend.storage.storage_manager import import_pool
from backend.storage.zfs_manager import (
    list_pools,
    list_datasets,
    create_pool,
    destroy_pool,
    import_pool,
)
from typing import Any, Optional

async def rpc_list_pools() -> Any:
    return await list_pools()

async def rpc_list_datasets(pool: Optional[str] = None) -> Any:
    return await list_datasets(pool)
    
async def rpc_import_pool(name: str) -> Any:
    return await import_pool(name)    

async def rpc_create_pool(name: str, devices: list, raidz: Optional[str] = None, dryRun: bool = True, force: bool = False) -> Any:
    # keep compatibility with previous naming conventions
    if dryRun:
        return await zfs_manager.preview_create_pool(name, devices, raidz=raidz)
    return await create_pool(name, devices, raidz=raidz, force=force)

async def rpc_destroy_pool(name: str) -> Any:
    ok = await destroy_pool(name)
    return {"ok": bool(ok)}

def register_rpc(register):
    register("zfs", {
        "listPools": rpc_list_pools,
        "listDatasets": rpc_list_datasets,
        "importpool" : rpc_import_pool,
        "createPool": rpc_create_pool,
        "destroyPool": rpc_destroy_pool,
    })
