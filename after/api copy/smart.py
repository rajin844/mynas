from fastapi import APIRouter
from backend.storage.smart_manager import smart_scan_all, smart_scan_disk

router = APIRouter()

@router.post("/scan")
async def api_scan_all():
    res = await smart_scan_all()
    return {"response": res, "error": None}

@router.post("/scan/disk")
async def api_scan_disk(payload: dict):
    dev = payload.get("devpath")
    if not dev:
        raise HTTPException(400, "devpath required")
    res = await smart_scan_disk(dev)
    return {"response": res, "error": None}
