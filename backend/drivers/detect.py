# backend/drivers/detect.py
import subprocess, json
from typing import List, Dict, Any

def detect_disks() -> List[Dict[str, Any]]:
    try:
        out = subprocess.check_output(["lsblk","-J","-o","NAME,KNAME,SIZE,MODEL,ROTA,MOUNTPOINT,TYPE"]).decode()
        j = json.loads(out)
        disks = []
        for d in j.get("blockdevices", []):
            if d.get("type") == "disk":
                disks.append({
                    "name": d.get("name"),
                    "devpath": "/dev/" + d.get("kname"),
                    "size": d.get("size"),
                    "model": d.get("model"),
                    "rotational": bool(d.get("rota")),
                    "mountpoint": d.get("mountpoint")
                })
        return disks
    except Exception:
        return []
