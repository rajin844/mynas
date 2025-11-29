from fastapi import APIRouter, HTTPException, Body
#from backend.storage.smart_manager import smart_scan_all
from backend.storage import smart_manager
router = APIRouter()

@router.post("/scan")
async def api_smart_scan():
    try:
        res = await smart_scan_all()
        return {"response": res, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan/disk")
async def api_scan_disk(payload: dict):
    dev = payload.get("devpath")
    if not dev:
        raise HTTPException(400, "devpath required")
    res = await smart_scan_disk(dev)
    return {"response": res, "error": None}
