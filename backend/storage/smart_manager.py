# backend/storage/smart_manager.py
import logging
from typing import Dict, Any, List
from backend.app.safe_exec import safe_exec
from backend.drivers.storage_driver_mysql import (
    list_disks_db,
    get_disk_by_devpath,
    get_disk_by_name,
    list_datasets_db,
    create_pool_record,
    add_pool_device,
    create_dataset_record,
    remove_pool_record,
)
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.smart_manager")



async def smart_scan_disk(devpath: str) -> Dict[str, Any]:
    r = await safe_exec(["smartctl", "-a", "-j", devpath], timeout=15, sudo=True)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("stderr")}
    import json
    try:
        j = json.loads(r["stdout"])
        temp = None
        if "temperature" in j and "current" in j["temperature"]:
            temp = j["temperature"]["current"]
        status = "PASSED" if j.get("smart_status", {}).get("passed", False) else "FAILED"
        return {"ok": True, "raw": j, "temperature": temp, "status": status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def smart_scan_all():
    disks = await driver.list_disks_db()
    out = []
    for d in disks:
        dev = d.get("devpath")
        try:
            r = await smart_scan_disk(dev)
            if not r.get("ok"):
                continue
            await add_smart_history(d.get("name"), r["raw"], r["status"], r.get("temperature"))
            if r["status"] != "PASSED":
                await push_alert("CRITICAL", f"SMART:{d.get('name')}", f"SMART failed for {d.get('name')}")
                await WSManagerProxy.broadcast({"module": "smart", "event": "disk_failed", "disk": d.get("name")})
            out.append({"name": d.get("name"), "status": r["status"], "temp": r.get("temperature")})
        except Exception:
            logger.exception("smart scan error for %s", dev)
    # broadcast result
    await WSManagerProxy.broadcast({"module": "smart", "event": "scan_complete", "result": out})
    return out
