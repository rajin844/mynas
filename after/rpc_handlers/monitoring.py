# backend/rpc_handlers/monitoring.py
"""
Monitoring RPC Handlers for MyNAS
Provides real-time system usage for CPU, RAM, Disk, Network.
"""

import logging
logger = logging.getLogger("mynas.rpc.monitor")

from backend.app.monitoring_manager import (
    get_system_metrics,
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    get_network_usage,
)

# -----------------------------
# RPC Methods
# -----------------------------

def rpc_metrics() -> dict:
    """Return full system metrics in one dictionary."""
    return get_system_metrics()


def rpc_cpu() -> float:
    """Return CPU usage percent."""
    return get_cpu_usage()


def rpc_memory() -> float:
    """Return RAM usage percent."""
    return get_memory_usage()


def rpc_disk() -> float:
    """Return disk (root FS) usage percent."""
    return get_disk_usage()


def rpc_network() -> dict:
    """Return upload/download (B/s)."""
    return get_network_usage()


def rpc_history(period: str = "1h") -> dict:
    """
    Placeholder for future detailed metrics history.
    TODO: Implement RRD/Time-Series logging system
    """
    return {
        "period": period,
        "supported": False,
        "message": "History logging not implemented yet.",
    }


# -----------------------------
# Register RPC
# -----------------------------

def register_rpc(register):
    """
    Register all RPC functions under service name: monitor
    """
    register("monitor", {
        "metrics": rpc_metrics,
        "cpu": rpc_cpu,
        "memory": rpc_memory,
        "disk": rpc_disk,
        "network": rpc_network,
        "history": rpc_history,
    })
