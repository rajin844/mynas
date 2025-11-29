# backend/api/storage.py
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from backend.storage import storage_manager

router = APIRouter()

@router.post("/summary")
async def api_storage_summary():
    try:
        res = await storage_manager.get_storage_summary()
        return {"response": res, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/listdisks")
async def api_list_disks():
    try:
        res = await storage_manager.list_disks()
        return {"response": res, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/createpool")
async def api_create_pool(payload: Dict[str, Any] = Body(...)):
    name = payload.get("name")
    devices = payload.get("devices")
    raidz = payload.get("raidz")
    dry = payload.get("dryRun", True)
    force = payload.get("force", False)
    if not name or not devices:
        raise HTTPException(status_code=400, detail="name and devices required")
    try:
        res = await storage_manager.create_zfs_pool(name, devices, raidz=raidz, dry_run=dry, force=force)
        return {"response": res, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/destroypool")
async def api_destroy_pool(payload: Dict[str, Any] = Body(...)):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    res = await storage_manager.destroy_zfs_pool(name)
    return {"response": res, "error": None}
