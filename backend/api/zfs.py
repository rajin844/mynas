# backend/api/zfs.py
from fastapi import APIRouter, HTTPException, Body
from typing import Any, Dict, List
from backend.storage.storage_manager import list_pools
from backend.storage.zfs_manager import list_datasets_api, create_dataset_api


router = APIRouter()

@router.post("/listpools")
def api_list_pools():
    return {"response": list_pools(), "error": None}


@router.post("/listdatasets")
def api_list_datasets(payload: dict = Body(None)):
    """
    Body may contain:
    { "pool": "tank" }
    or empty {}
    """
    pool = None
    if payload:
        pool = payload.get("pool")

    try:
        if pool:
            datasets = list_datasets_api(pool=pool)
        else:
            datasets = list_datasets_api()
        return {"response": datasets, "error": None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/createdataset")
def api_create_dataset(payload: dict = Body(...)):
    """
    Body must contain {pool:"tank", name:"data", mountpoint:"/mnt/tank/data"}
    """
    if "pool" not in payload or "name" not in payload:
        raise HTTPException(400, "Both 'pool' and 'name' are required")

    pool = payload["pool"]
    name = payload["name"]
    mount = payload.get("mountpoint")

    ok = create_dataset_api(pool, name, mount)

    return {"response": {"created": bool(ok)}, "error": None}
