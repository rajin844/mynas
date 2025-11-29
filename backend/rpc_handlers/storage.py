# backend/rpc_handlers/storage.py
"""
RPC handlers for storage service (async-aware)
Registered names: "storage"
Methods:
  - summary
  - list_disks
  - create_pool
  - destroy_pool
  - import_pool
"""
import logging
from typing import Any, Dict
from backend.storage import storage_manager

async def rpc_summary():
    return await storage_manager.get_storage_summary()

async def rpc_list_disks():
    return await storage_manager.list_disks()

async def rpc_create_pool(name: str, devices: list, raidz: str = None, dry_run: bool = True, force: bool = False):
    return await storage_manager.create_zfs_pool(name, devices, raidz=raidz, dry_run=dry_run, force=force)

async def rpc_destroy_pool(name: str):
    return await storage_manager.destroy_zfs_pool(name)

async def rpc_detectdisks():
    return await storage_manager.detect_disks()    

async def rpc_import_pool(name: str) -> Any:
    return await import_pool(name)


def register_rpc(register):
    register("storage", {
        "summary": rpc_summary,
        "listdisks": rpc_list_disks,
        "detectdisks": rpc_detectdisks,
        "create_pool": rpc_create_pool,
        "destroy_pool": rpc_destroy_pool,
        "import_pool": rpc_import_pool,
    })
