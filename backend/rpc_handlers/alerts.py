# backend/rpc_handlers/alerts.py
from backend.system.alerts_manager import list_alerts, ack_alert

def rpc_list():
    return list_alerts()

def rpc_ack(id):
    return ack_alert(id)

def register_rpc(register):
    register("alerts", {"list": rpc_list, "ack": rpc_ack})
