from fastapi import APIRouter
from backend.app.config_manager import ConfigManager

router = APIRouter()
cfg = ConfigManager()

@router.get("/interfaces")
def get_interfaces():
    n = cfg.get_section("network") or {}
    return n

@router.post("/set")
def set_iface(payload: dict):
    iface = payload.get("iface"); ip = payload.get("ip")
    n = cfg.get_section("network") or {}
    n[iface] = {"ip": ip}
    cfg.set_section("network", n)
    return {"ok": True}
