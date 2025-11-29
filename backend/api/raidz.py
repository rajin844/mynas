# backend/api/raidz.py
from fastapi import APIRouter, HTTPException, Body
from backend.storage.raidz_manager import build_raidz_layout

router = APIRouter()

@router.post("/preview")
async def api_preview(payload: dict = Body(...)):
    devices = payload.get("devices")
    level = payload.get("level", "single")
    if not devices:
        raise HTTPException(status_code=400, detail="devices required")
    try:
        layout = build_raidz_layout(devices, level)
        return {"response": layout, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
