# backend/app/monitor_broadcaster.py
import asyncio
from backend.system.monitoring_manager import get_system_metrics
from backend.realtime.websocket_server import WSManagerProxy

async def periodic_monitor(interval=5):
    while True:
        try:
            WSManagerProxy.broadcast({
                "module": "monitor",
                "event": "metrics",
                "data": get_system_metrics(),
            })
        except Exception as e:
            print("[Monitor] Error:", e)
        await asyncio.sleep(interval)
