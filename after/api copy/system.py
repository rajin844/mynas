# backend/api/system.py
from fastapi import APIRouter, HTTPException, Body
from backend.app.system_manager import (
    get_system_info,
    get_hostname,
    set_hostname,
    get_timezone,
    set_timezone,
    reboot_system,
    shutdown_system,
)

router = APIRouter()


@router.get("/info")
def api_system_info():
    return {"response": get_system_info(), "error": None}


@router.get("/hostname/get")
def api_hostname_get():
    return {"response": get_hostname(), "error": None}


@router.post("/hostname/set")
def api_hostname_set(payload: dict = Body(...)):
    try:
        return {"response": set_hostname(payload.get("hostname")), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/timezone/get")
def api_timezone_get():
    return {"response": get_timezone(), "error": None}


@router.post("/timezone/set")
def api_timezone_set(payload: dict = Body(...)):
    try:
        return {"response": set_timezone(payload.get("timezone")), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/reboot")
def api_reboot():
    try:
        return {"response": reboot_system(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/shutdown")
def api_shutdown():
    try:
        return {"response": shutdown_system(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
