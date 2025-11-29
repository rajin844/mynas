from fastapi import APIRouter, Body
from backend.storage.raidz_manager import preview_layout

router = APIRouter()

@router.post("/preview")
async def api_raidz_preview(payload: dict = Body(...)):
    devices = payload.get("devices", [])
    mode = payload.get("mode", "single")
    res = await preview_layout(devices, mode)
    return {"response": res, "error": None}
