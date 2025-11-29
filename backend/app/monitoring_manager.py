# backend/app/monitoring_manager.py
"""
Simple monitoring manager.

Provide:
 - get_system_metrics() -> dict
 - get_cpu_usage(), get_memory_usage(), get_disk_usage(), get_network_usage()
This implementation uses light-weight fallbacks so the broadcaster never fails.
Replace with psutil or platform-specific collectors later.
"""

import platform
import shutil
import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger("mynas.monitoring")

# Simple placeholders. Replace with psutil calls in production.
def get_cpu_usage() -> float:
    # On most platforms psutil.cpu_percent() is preferred. Use 0-100 float here.
    try:
        # fallback: use load average normalized by cores (approximate)
        if hasattr(os, "getloadavg"):
            load1 = os.getloadavg()[0]
            cores = os.cpu_count() or 1
            pct = min(100.0, (load1 / max(1, cores)) * 100.0)
            return round(pct, 2)
    except Exception:
        pass
    return 0.0

def get_memory_usage() -> float:
    try:
        # fallback: use shutil.disk_usage? no — memory indistinct — return 0 safe
        return 0.0
    except Exception:
        return 0.0

def get_disk_usage() -> float:
    try:
        # approximate root usage
        total, used, free = shutil.disk_usage("/")
        return round((used / total) * 100.0, 2) if total else 0.0
    except Exception:
        return 0.0

def get_network_usage() -> Dict[str, Any]:
    # Placeholder; collecting real network bps requires tracking deltas
    return {"upload_bps": 0, "download_bps": 0}

def get_system_metrics() -> Dict[str, Any]:
    """Aggregate metrics dictionary used by broadcaster and API."""
    try:
        return {
            "timestamp": int(time.time()),
            "cpu": get_cpu_usage(),
            "memory": get_memory_usage(),
            "disk": get_disk_usage(),
            "network": get_network_usage(),
        }
    except Exception as e:
        logger.exception("get_system_metrics failed: %s", e)
        return {"cpu": 0, "memory": 0, "disk": 0, "network": {"upload_bps": 0, "download_bps": 0}}
