# backend/api/zfs.py
"""
ZFS REST API (DB + safe_exec backend)
"""

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any

from backend.storage.zfs_manager import (
    list_pools,
    list_datasets,
    create_pool,
    destroy_pool,
    import_pool,
)

router = APIRouter()


# -------------------------------------------------------------
@router.post("/listpools")
async def api_list_pools():
    try:
        data = await list_pools()
        return {"response": data, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


# -------------------------------------------------------------
@router.post("/listdatasets")
async def api_list_datasets(payload: Dict[str, Any] = Body(None)):
    pool = None
    if payload:
        pool = payload.get("pool")

    try:
        data = await list_datasets(pool)
        return {"response": data, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


# -------------------------------------------------------------
@router.post("/createdataset")
async def api_create_dataset(payload: Dict[str, Any] = Body(...)):
    pool = payload.get("pool")
    name = payload.get("name")
    mount = payload.get("mountpoint")

    if not pool or not name:
        raise HTTPException(400, "pool & name required")

    try:
        res = await create_pool(pool, [name], raidz=None)   # dataset
        return {"response": res, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/importpool")
async def api_import(payload: dict):
    return {"response": await import_pool(payload["pool"]), "error": None}


# -------------------------------------------------------------
@router.post("/destroydataset")
async def api_destroy_dataset(payload: Dict[str, Any] = Body(...)):
    pool = payload.get("pool")
    name = payload.get("name")
    if not pool or not name:
        raise HTTPException(400, "pool and name required")

    try:
        res = await destroy_pool(name)  # dataset destroy dispatches correctly
        return {"response": res, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
