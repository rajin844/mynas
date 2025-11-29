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
from backend.storage import zfs_manager

async def rpc_list_pools():
    return await zfs_manager.list_pools()

async def rpc_list_datasets(pool: str = None):
    return await zfs_manager.list_datasets(pool)

async def rpc_create_pool(name: str, devices: list, raidz: str = None, dryRun: bool = True, force: bool = False):
    # note: dryRun naming compatibility
    return await zfs_manager.preview_create_pool(name, devices, raidz) if dryRun else await zfs_manager.create_pool(name, devices, raidz=raidz, force=force)

async def rpc_destroy_pool(name: str):
    return await zfs_manager.destroy_pool(name)
from typing import Any, Optional

async def rpc_import_pool(name: str) -> Any:
    return await  zfs_manager.import_pool(name)    

#async def rpc_create_pool(name: str, devices: list, raidz: Optional[str] = None, dryRun: bool = True, force: bool = False) -> Any:
    # keep compatibility with previous naming conventions
 #   if dryRun:
  #      return await zfs_manager.preview_create_pool(name, devices, raidz=raidz)
   # return await zfs_manager.create_pool(name, devices, raidz=raidz, force=force)

def register_rpc(register):
    register("zfs", {
        "listPools": rpc_list_pools,
        "listDatasets": rpc_list_datasets,
        "importpool" : rpc_import_pool,
        "createPool": rpc_create_pool,
        "destroyPool": rpc_destroy_pool,
    })
