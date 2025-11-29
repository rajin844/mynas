# backend/api/monitoring.py
from fastapi import APIRouter, HTTPException
from backend.app.monitoring_manager import (
    get_system_metrics,
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    get_network_usage,
)

router = APIRouter()

@router.get("/metrics")
def api_all_metrics():
    try:
        return {"response": get_system_metrics(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/cpu")
def api_cpu():
    return {"response": get_cpu_usage(), "error": None}


@router.get("/memory")
def api_memory():
    return {"response": get_memory_usage(), "error": None}


@router.get("/disk")
def api_disk():
    return {"response": get_disk_usage(), "error": None}


@router.get("/network")
def api_network():
    return {"response": get_network_usage(), "error": None}
