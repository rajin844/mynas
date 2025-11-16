# backend/api/storage.py
from fastapi import APIRouter, HTTPException
from backend.storage.storage_manager import (
    list_disks,
    detect_disks,
   disk_usage,
   smart_health,
    get_storage_summary,
)

router = APIRouter()

@router.post("/listdisks")
def api_list_disks():
    try:
        return {"response": list_disks(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/detect")
def api_detect_disks():
    try:
        return {"response": detect_disks(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/usage")
def api_disk_usage(device: str):
    try:
        return {"response": disk_usage(device), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/smart")
def api_smart_info(device: str):
    try:
        return {"response": smart_health(device), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/summary")
def api_storage_summary():
    try:
        return {"response": get_storage_summary(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
