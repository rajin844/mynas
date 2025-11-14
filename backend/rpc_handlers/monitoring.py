# backend/rpc_handlers/monitoring.py
"""
RPC handlers for monitoring: get_stats
Service: "monitoring"
"""

import psutil
from typing import Dict, Any

def rpc_get_stats() -> Dict[str, Any]:
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent
    }

def register_rpc(register):
    register("monitoring", {
        "get_stats": rpc_get_stats
    })
