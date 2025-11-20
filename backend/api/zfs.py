# backend/api/zfs.py
from fastapi import APIRouter, HTTPException, Body
from backend.storage.zfs_manager import list_pools, list_datasets, create_pool
from backend.storage.zfs_manager import list_pools, list_datasets, create_dataset, destroy_dataset


@router.post("/listpools")
def api_list_pools():
    return {"response": list_pools(), "error": None}

@router.post("/listdatasets")
def api_list_datasets(payload: dict = Body(None)):
    pool = payload.get("pool") if payload else None
    return {"response": list_datasets(pool), "error": None}


@router.post("/createpool")
def api_create_pool(payload: dict = Body(...)):
    return {"response": create_pool(
        payload["name"], payload["layout"], payload.get("dry_run", False)
    ), "error": None}

@router.post("/createdataset")
def api_create_dataset(payload: dict = Body(...)):
    pool = payload.get("pool"); name = payload.get("name"); mount = payload.get("mountpoint")
    return {"response": create_dataset(pool, name, mount), "error": None}