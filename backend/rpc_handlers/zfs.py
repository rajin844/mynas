# backend/rpc_handlers/zfs.py
from typing import Any, Dict
from backend.storage.zfs_manager import list_pools, list_datasets, create_pool, destroy_pool
from backend.storage.zfs_manager import create_dataset, destroy_dataset, list_datasets

def rpc_listdatasets(pool: str = None):
    return list_datasets(pool=pool)

def rpc_createpool(name: str, devices: list, raidz: str = None, dry_run: bool = True):
    return create_pool(name, devices, raidz=raidz, dry_run=dry_run)

def rpc_listpools():
    return list_pools()

def rpc_list_datasets(pool: str=None):
    return list_datasets(pool)

def rpc_create_dataset(pool: str, name: str, mountpoint: str=None):
    return create_dataset(pool, name, mountpoint)

def rpc_destroy_dataset(pool: str, name: str):
    return destroy_dataset(pool, name)

def register_rpc(register):
    register("zfs", {
        "listpools"   : rpc_listpools,
        "listdatasets": rpc_list_datasets,
        "createdataset": rpc_create_dataset,
        "destroydataset": rpc_destroy_dataset,
    })

from backend.storage.storage_manager import *

def register_rpc(register):
         register("zfs", {
        "listPools": list_pools,
        "createPool": create_pool,
        "destroyPool": destroy_pool,
        "listDatasets": list_datasets,
        "createDataset": create_dataset,
        "destroyDataset": destroy_dataset,
         })  

         