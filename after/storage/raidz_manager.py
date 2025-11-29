# backend/storage/raidz_manager.py
"""
RAIDZ builder + preview utilities.
- build_layout(devices, mode) -> topology
- preview_layout(...) -> returns quick capacity/shape estimate
"""

import logging
from typing import List, Dict, Any
import math

from backend.realtime.websocket_server import WSManagerProxy
from backend.drivers import db

logger = logging.getLogger("mynas.raidz")


def build_layout(devices: List[str], mode: str) -> Dict[str, Any]:
    mode = (mode or "single").lower()
    if mode == "single":
        return {"vdevs": [{"type": "single", "disks": devices}]}
    if mode == "mirror":
        if len(devices) < 2:
            raise ValueError("mirror needs >=2")
        return {"vdevs": [{"type": "mirror", "disks": devices}]}
    if mode.startswith("raidz"):
        # raidz1/2/3 -> parity count = trailing digit (1/2/3)
        return {"vdevs": [{"type": mode, "disks": devices}]}
    return {"vdevs": [{"type": "single", "disks": devices}]}


async def preview_layout(devices: List[str], mode: str) -> Dict[str, Any]:
    """
    Provide size estimate: find smallest disk size from DB (or return None)
    and estimate usable capacity for mirror/raidz1/2/3 (naive).
    """
    try:
        sizes_gb = []
        for d in devices:
            r = await db.fetchrow("SELECT size FROM disks WHERE devpath=%s OR name=%s LIMIT 1", (d, d))
            if r and r.get("size"):
                val = r["size"]
                # try to parse strings like '200G' or numeric (approx)
                try:
                    if isinstance(val, (int, float)):
                        sizes_gb.append(float(val))
                    else:
                        # remove non-digits
                        s = str(val).upper().replace("G", "").replace("M", "")
                        sizes_gb.append(float(s))
                except Exception:
                    pass
        smallest = min(sizes_gb) if sizes_gb else None
        topology = build_layout(devices, mode)
        usable = None
        if smallest:
            if mode == "single":
                usable = smallest * len(devices)
            elif mode == "mirror":
                usable = smallest
            elif mode.startswith("raidz"):
                parity = int(mode[-1]) if mode[-1].isdigit() else 1
                usable = smallest * max(0, len(devices) - parity)
        return {"topology": topology, "size_estimate_gb": usable, "smallest_gb": smallest}
    except Exception as e:
        logger.exception("preview_layout failed: %s", e)
        return {"error": str(e)}
