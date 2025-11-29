# backend/api/storage.py
"""
Storage REST API (MySQL-backed)
Handles:
 - list disks
 - storage summary
 - pool preview (dry-run)
 - actual pool creation
 - pool destroy
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List

from backend.storage.storage_manager import (
    detect_disks,
    list_disks_out,
    list_disks_db,
    get_storage_summary,
    create_zfs_pool,
    import_pool,
    destroy_zfs_pool,
)

router = APIRouter()

# -------------------------------------------------------------
@router.post("/listdisks")
async def api_list_disks():
    try:
        disks = await list_disks_out()
        return {"response": disks, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------------
# REFRESH DISKS (forced detect)
# ---------------------------------------------------------
@router.post("/refresh")
async def api_refresh_disks():
    try:
        updated = await detect_disks()
        return {"response": updated, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------------
# STORAGE SUMMARY
# ---------------------------------------------------------
@router.post("/summary")
async def api_storage_summary():
    try:
        summary = await get_storage_summary()
        return {"response": summary, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

# -------------------------------------------------------------
@router.post("/createpool")
async def api_create_pool(payload: Dict[str, Any] = Body(...)):
    """
    {
      "name": "main",
      "devices": ["/dev/sda", "/dev/sdb"],
      "raidz": "raidz1",
      "dryRun": true,
      "force": false
    }
    """
    name = payload.get("name")
    devices = payload.get("devices")
    raidz = payload.get("raidz")
    dry_run = payload.get("dryRun", True)
    force = payload.get("force", False)

    if not name or not devices:
        raise HTTPException(400, "name and devices required")

    res = await create_zfs_pool(name, devices, raidz=raidz, dry_run=dry_run, force=force)
    return {"response": res, "error": None}


# -------------------------------------------------------------
@router.post("/destroypool")
async def api_destroy_pool(payload: Dict[str, Any] = Body(...)):
    name = payload.get("name")
    if not name:
        raise HTTPException(400, "name required")

    res = await destroy_zfs_pool(name)
    return {"response": res, "error": None}

@router.post("/alerts")
async def api_storage_alerts():
    from backend.storage.storage_manager import get_storage_alerts
    alerts = await get_storage_alerts()
    return {"response": alerts, "error": None}    


@router.post("/importpool")
async def api_import_pool(payload: Dict[str, Any] = Body(...)):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    try:
        res = await storage_manager.import_pool(name)
        return {"response": res, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
