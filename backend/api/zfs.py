# backend/api/zfs.py
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from backend.storage import zfs_manager

router = APIRouter()

@router.post("/listpools")
async def api_list_pools():
    try:
        pools = await zfs_manager.list_pools()
        return {"response": pools, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/listdatasets")
async def api_list_datasets(payload: Optional[Dict[str, Any]] = Body(None)):
    pool = payload.get("pool") if payload else None
    try:
        ds = await zfs_manager.list_datasets(pool)
        return {"response": ds, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/createdataset")
async def api_create_dataset(payload: Dict[str, Any] = Body(...)):
    pool = payload.get("pool")
    name = payload.get("name")
    mount = payload.get("mountpoint")
    if not pool or not name:
        raise HTTPException(status_code=400, detail="pool and name required")
    try:
        res = await zfs_manager.create_dataset(pool, name, mountpoint=mount)
        return {"response": res, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/destroydataset")
async def api_destroy_dataset(payload: Dict[str, Any] = Body(...)):
    pool = payload.get("pool")
    name = payload.get("name")
    if not pool or not name:
        raise HTTPException(status_code=400, detail="pool and name required")
    res = await zfs_manager.destroy_dataset(pool, name)
    return {"response": res, "error": None}
