# backend/app/monitor_broadcaster.py

import asyncio
import psutil
from backend.realtime.websocket_server import WSManagerProxy
import time

_last_net_rx = 0
_last_net_tx = 0
_last_check_time = time.time()


def get_system_metrics():
    """Collect system resource usage."""

    # CPU %
    cpu = psutil.cpu_percent(interval=None)

    # RAM
    mem = psutil.virtual_memory()
    ram = mem.percent

    # Disk usage (root fs)
    disk = psutil.disk_usage("/").percent

    # Network BPS (download/upload calculation)
    global _last_net_rx, _last_net_tx, _last_check_time

    net = psutil.net_io_counters()
    now = time.time()
    dt = now - _last_check_time if _last_check_time else 1

    download_bps = (net.bytes_recv - _last_net_rx) / dt
    upload_bps = (net.bytes_sent - _last_net_tx) / dt

    _last_net_rx = net.bytes_recv
    _last_net_tx = net.bytes_sent
    _last_check_time = now

    return {
        "cpu": cpu,
        "memory": ram,
        "disk": disk,
        "network": {
            "download_bps": download_bps,
            "upload_bps": upload_bps,
        }
    }


async def periodic_monitor():
    while True:
        try:
            metrics = get_system_metrics()

            await WSManagerProxy.broadcast({
                "module": "monitor",
                "data": metrics
            })

        except Exception as e:
            print(f"[ERROR] Monitoring broadcast error: {e}")

        await asyncio.sleep(5)
