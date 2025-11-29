"""
backend/api/system.py
---------------------
REST API for system settings & system info.
Backed by system_manager.py (no ConfigManager).
"""

from fastapi import APIRouter, HTTPException, Body
from backend.app.system_manager import (
    system_summary,
    get_hostname,
    set_hostname,
    get_timezone,
    set_timezone,
    system_reboot,
    system_shutdown,
)

router = APIRouter()


# ===========================================================
# 🖥️ SYSTEM SUMMARY (Dashboard)
# ===========================================================

@router.post("/summary")
async def api_system_summary():
    try:
        return {"response": await system_summary(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


# ===========================================================
# 🏷️ HOSTNAME
# ===========================================================

@router.post("/hostname/get")
async def api_get_hostname():
    return {"response": await get_hostname(), "error": None}


@router.post("/hostname/set")
async def api_set_hostname(payload: dict = Body(...)):
    name = payload.get("hostname")
    if not name:
        raise HTTPException(400, "hostname is required")

    ok = await set_hostname(name)
    return {"response": {"updated": ok}, "error": None}


# ===========================================================
# 🌐 TIMEZONE
# ===========================================================

@router.post("/timezone/get")
async def api_get_timezone():
    return {"response": await get_timezone(), "error": None}


@router.post("/timezone/set")
async def api_set_timezone(payload: dict = Body(...)):
    tz = payload.get("timezone")
    if not tz:
        raise HTTPException(400, "timezone is required")

    ok = await set_timezone(tz)
    return {"response": {"updated": ok}, "error": None}


# ===========================================================
# 🔧 SYSTEM ACTIONS
# ===========================================================

@router.post("/reboot")
async def api_reboot():
    ok = await system_reboot()
    return {"response": {"rebooting": ok}, "error": None}


@router.post("/shutdown")
async def api_shutdown():
    ok = await system_shutdown()
    return {"response": {"shutdown": ok}, "error": None}
