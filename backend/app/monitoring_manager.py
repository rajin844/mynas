# backend/app/monitoring_manager.py
"""
System Monitoring Manager
Used by both REST API + WebSocket monitoring broadcaster.
"""

import psutil
import time

_last_rx = 0
_last_tx = 0
_last_time = time.time()


# ===========================
# MAIN SYSTEM METRICS
# ===========================
def get_system_metrics():
    """Return CPU, RAM, Disk, Network usage in one dict."""
    return {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
        "network": get_network_usage(),
    }


# ===========================
# CPU %
# ===========================
def get_cpu_usage():
    return psutil.cpu_percent(interval=None)


# ===========================
# MEMORY %
# ===========================
def get_memory_usage():
    return psutil.virtual_memory().percent


# ===========================
# DISK USAGE %
# ===========================
def get_disk_usage():
    try:
        return psutil.disk_usage("/").percent
    except:
        return 0


# ===========================
# NETWORK USAGE (bytes/sec)
# ===========================
def get_network_usage():
    global _last_rx, _last_tx, _last_time

    counters = psutil.net_io_counters()
    now = time.time()
    dt = now - _last_time if _last_time else 1

    download_bps = (counters.bytes_recv - _last_rx) / dt
    upload_bps = (counters.bytes_sent - _last_tx) / dt

    _last_rx = counters.bytes_recv
    _last_tx = counters.bytes_sent
    _last_time = now

    return {
        "download_bps": download_bps,
        "upload_bps": upload_bps,
    }
