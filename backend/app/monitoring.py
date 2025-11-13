"""
Monitoring helpers using psutil.
Provides functions to get cpu/memory/disk stats and an optional
async broadcaster wrapper for periodic pushes.
"""

import psutil
import asyncio
from typing import Dict
from backend.realtime.websocket_server import WSManagerProxy

def get_cpu_percent(interval: float = 0.5) -> float:
    """Return CPU percent (0-100)."""
    return psutil.cpu_percent(interval=interval)


def get_memory_percent() -> float:
    mem = psutil.virtual_memory()
    return mem.percent


def get_disk_percent(path: str = "/") -> float:
    return psutil.disk_usage(path).percent


async def periodic_broadcast(interval: float = 5.0):
    """
    Periodically broadcast monitoring data to connected websocket clients.
    Use: asyncio.create_task(periodic_broadcast()) from your startup code.
    """
    while True:
        try:
            data: Dict = {
                "module": "monitoring",
                "cpu": int(get_cpu_percent(0.1)),
                "memory": int(get_memory_percent()),
                "disk": int(get_disk_percent("/")),
            }
            # broadcast best-effort
            try:
                WSManagerProxy.broadcast(data)
            except Exception:
                pass
        except Exception:
            pass
        await asyncio.sleep(interval)
