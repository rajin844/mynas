# backend/api/storage.py
"""
Storage API for MyNAS.
Handles ZFS pools, datasets, and general storage operations.

Endpoints:
POST /api/storage/listpools
POST /api/storage/listdatasets
POST /api/storage/createpool
POST /api/storage/destroypool
POST /api/storage/createdataset
POST /api/storage/destroydataset
"""

from fastapi import APIRouter, HTTPException, Body

# Prefer backend.storage.* modules
try:
    from backend.storage.zfs_manager import (
       list_datasets_api,
       create_dataset_api,
       delete_dataset_api,
       modify_dataset_api,
    )
except Exception:
    # fallback if directory structure uses app.storage.*
    from backend.storage.zfs_manager import (
       list_datasets_api,
       create_dataset_api,
       delete_dataset_api,
       modify_dataset_api,
    )

# Storage database sync
try:
    from backend.storage.storage_manager import list_pools, create_pool_api, import_pool_api, destroy_pool_api
except:
    from backend.storage.storage_manager import list_pools, create_pool_api, import_pool_api, destroy_pool_api


router = APIRouter()

# -------------------------------------------------------------
# Pools
# -------------------------------------------------------------

@router.post("/listpools")
def api_list_pools():
    """
    Return list of existing ZFS pools.
    """
    pools = list_pools
    return {"response": pools, "error": None}


@router.post("/createpool")
def api_create_pool(payload: dict = Body(...)):
    """
    Body:
    {
        "name": "tank",
        "devices": ["/dev/sda", "/dev/sdb"]
    }
    """
    name = payload.get("name")
    devices = payload.get("devices")

    if not name or not devices:
        raise HTTPException(400, "name and devices required")

    ok = create_zfs_pool(name, devices)
    if ok:
        add_pool(name, devices)

    return {"response": {"created": bool(ok)}, "error": None}


@router.post("/destroypool")
def api_destroy_pool(payload: dict = Body(...)):
    """
    Body:
    {
        "name": "tank"
    }
    """
    name = payload.get("name")
    if not name:
        raise HTTPException(400, "name required")

    ok = destroy_zfs_pool(name)
    if ok:
        remove_pool(name)

    return {"response": {"deleted": bool(ok)}, "error": None}


# -------------------------------------------------------------
# Datasets
# -------------------------------------------------------------

@router.post("/listdatasets")
def api_list_datasets(payload: dict = Body(None)):
    """
    Body:
    { "pool": "tank" }
    or
    {}
    """
    pool = payload.get("pool") if payload else None
    datasets = list_zfs_datasets(pool)
    return {"response": datasets, "error": None}


@router.post("/createdataset")
def api_create_dataset(payload: dict = Body(...)):
    """
    Body:
    {
        "pool": "tank",
        "name": "data",
        "mountpoint": "/mnt/tank/data" (optional)
    }
    """
    pool = payload.get("pool")
    name = payload.get("name")
    mount = payload.get("mountpoint")

    if not pool or not name:
        raise HTTPException(400, "pool and name required")

    ok = create_zfs_dataset(pool, name, mount)

    if ok:
        add_dataset(pool, name, mount)

    return {"response": {"created": bool(ok)}, "error": None}


@router.post("/destroydataset")
def api_destroy_dataset(payload: dict = Body(...)):
    """
    Body:
    {
        "pool": "tank",
        "name": "data"
    }
    """
    pool = payload.get("pool")
    name = payload.get("name")

    if not pool or not name:
        raise HTTPException(400, "pool and name required")

    ok = destroy_zfs_dataset(pool, name)

    if ok:
        remove_dataset(pool, name)

    return {"response": {"deleted": bool(ok)}, "error": None}


