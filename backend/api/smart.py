# backend/api/smart.py
from fastapi import APIRouter, HTTPException, Body
from backend.app.smart import smart_health

router = APIRouter()

@router.post("/info")
def api_smart_info(payload: dict = Body(...)):
    """
    Payload:
    { "device": "/dev/sda" }
    """
    device = payload.get("device")
    if not device:
        raise HTTPException(400, "device path required")

    try:
        data = smart_health(device)
        return {"response": data, "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
