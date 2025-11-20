# backend/api/alerts.py
from fastapi import APIRouter
from backend.system.alerts_manager import list_alerts, ack_alert

router = APIRouter()

@router.post("/list")
def api_list():
    return {"response": list_alerts(), "error": None}

@router.post("/ack")
def api_ack(payload: dict):
    return {"response": ack_alert(payload.get("id")), "error": None}
