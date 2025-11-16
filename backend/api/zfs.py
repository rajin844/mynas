# backend/api/zfs.py
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from backend.storage.zfs_manager import (
    list_pools,
    pool_status,
    create_pool,
    destroy_pool,
    import_pool,
    export_pool,
    list_datasets,
    create_dataset,
    destroy_dataset,
)

router = APIRouter()

# ------- POOLS -------

@router.post("/listpools")
def api_list_pools():
    try:
        return {"response": list_pools(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/pool/status")
def api_pool_status(name: str):
    try:
        return {"response": pool_status(name), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/pool/create")
def api_create_pool(payload: dict = Body(...)):
    name = payload.get("name")
    devices = payload.get("devices")
    raidz = payload.get("raidz")
    dry = payload.get("dryRun", True)

    if not name or not devices:
        raise HTTPException(400, "Pool name + devices required")

    try:
        return {
            "response": create_pool(name, devices, raidz=raidz, dryRun=dry),
            "error": None,
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/pool/destroy")
def api_destroy_pool(payload: dict = Body(...)):
    name = payload.get("name")
    if not name:
        raise HTTPException(400, "Pool name required")
    try:
        return {"response": destroy_pool(name), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/pool/import")
def api_import_pool(name: str):
    return {"response": import_pool(name), "error": None}

@router.post("/pool/export")
def api_export_pool(name: str):
    return {"response": export_pool(name), "error": None}

# ------- DATASETS -------

@router.post("/listdatasets")
def api_list_datasets(payload: Dict[str, Any] = Body(None)):
    try:
        pool = payload.get("pool") if payload else None
        return {"response": list_datasets(pool), "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dataset/create")
def api_create_dataset(payload: dict = Body(...)):
    pool = payload.get("pool")
    name = payload.get("name")
    mountpoint = payload.get("mountpoint")

    if not pool or not name:
        raise HTTPException(400, "Pool + dataset name required")

    try:
        return {
            "response": create_dataset(pool, name, mountpoint=mountpoint),
            "error": None,
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/dataset/destroy")
def api_destroy_dataset(payload: dict = Body(...)):
    pool = payload.get("pool")
    name = payload.get("name")

    if not pool or not name:
        raise HTTPException(400, "Pool + dataset name required")

    try:
        return {"response": destroy_dataset(pool, name), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
