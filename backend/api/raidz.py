# backend/api/raidz.py
from fastapi import APIRouter, HTTPException, Body
from backend.app.raidz import build_raidz_layout

router = APIRouter()

@router.post("/build")
def api_build_raidz(payload: dict = Body(...)):
    """
    Payload:
    {
        "devices": ["/dev/sda", "/dev/sdb", "/dev/sdc"],
        "level": "raidz1"
    }
    """
    devices = payload.get("devices")
    level = payload.get("level", "raidz1")

    if not devices or len(devices) < 2:
        raise HTTPException(400, "At least 2 devices required")

    try:
        layout = build_raidz_layout(devices, level)
        return {"response": layout, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
