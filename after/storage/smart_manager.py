# backend/storage/smart_manager.py
"""
SMART manager:
- smart_scan_disk(devpath) -> returns SMART JSON
- smart_scan_all() -> iterate disks, store to DB table smart_history
- add_smart_history helper writes DB
- broadcasts 'smart' WS events on failures/updates
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from backend.drivers import db
from backend.app.safe_exec import safe_exec
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.smart_manager")


async def add_smart_history(disk_name: str, raw: Dict[str, Any], status: str, temp_c: Any):
    try:
        await db.exec(
            "INSERT INTO smart_history (disk_name, raw_json, status, temp_c, created_at) VALUES (%s,%s,%s,%s,NOW())",
            (disk_name, json.dumps(raw), status, temp_c)
        )
    except Exception:
        # table may not exist
        pass


async def smart_scan_disk(devpath: str) -> Dict[str, Any]:
    """Run smartctl -j and return parsed JSON"""
    try:
        r = await safe_exec(["smartctl", "-a", "-j", devpath], timeout=15, sudo=True)
        if not r.get("ok"):
            return {"ok": False, "error": r.get("stderr")}
        try:
            data = json.loads(r["stdout"])
        except Exception:
            return {"ok": False, "error": "invalid smart JSON"}
        temp = None
        try:
            temp = data.get("temperature", {}).get("current")
        except Exception:
            temp = None
        health = data.get("smart_status", {}).get("passed")
        return {"ok": True, "raw": data, "temperature": temp, "health": "PASSED" if health else "FAILED"}
    except Exception as e:
        logger.exception("smart_scan_disk failed: %s", e)
        return {"ok": False, "error": str(e)}


async def smart_scan_all() -> List[Dict[str, Any]]:
    """
    Scan all known disks. Use disks table or detect_disks().
    Stores history & broadcasts events.
    """
    out = []
    try:
        disks = await db.fetchall("SELECT name, devpath FROM disks")
        if not disks:
            # fallback use lsblk via storage_manager
            from backend.storage.storage_manager import detect_disks
            disks = await detect_disks()

        for d in disks:
            dev = d.get("devpath") or d.get("path") or d.get("name")
            if not dev:
                continue
            res = await smart_scan_disk(dev)
            if res.get("ok"):
                await add_smart_history(d.get("name") or dev, res["raw"], res["health"], res.get("temperature"))
                # broadcast per-disk update
                await WSManagerProxy.broadcast({
                    "module": "smart",
                    "event": "disk_update",
                    "data": {"disk": d.get("name") or dev, "health": res.get("health"), "temp": res.get("temperature")}
                })
                out.append({"disk": d.get("name") or dev, "health": res.get("health"), "temp": res.get("temperature")})
            else:
                out.append({"disk": d.get("name") or dev, "error": res.get("error")})
        return out
    except Exception as e:
        logger.exception("smart_scan_all failed: %s", e)
        return out
