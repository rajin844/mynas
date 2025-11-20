# backend/api/network.py
from fastapi import APIRouter, HTTPException, Body
from backend.app.network_manager import (
    get_interfaces,
    update_network,
    restart_network,
)

router = APIRouter()

@router.post("/interfaces")
def api_interfaces():
    return {"response": get_interfaces(), "error": None}

@router.post("/update")
def api_update(payload: dict = Body(...)):
    try:
        return {"response": update_network(payload), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
 
@router.post("/apply")
def api_apply(payload: dict = Body(...)):
    return {"response": apply_network_settings(payload), "error": None}       

@router.post("/restart")
def api_restart():
    return {"response": restart_network(), "error": None}
