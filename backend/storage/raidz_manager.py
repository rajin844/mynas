# backend/storage/raidz_manager.py
from typing import List, Dict, Any, Tuple
import logging
from backend.app.config_manager import cfg


logger = logging.getLogger("mynas.raidz_manager")

def human_size_bytes_to_str(b: int) -> str:
    # quick helper
    for unit in ['B','KB','MB','GB','TB','PB']:
        if b < 1024:
            return f"{b}{unit}"
        b = b // 1024
    return f"{b}PB"

def parse_disk_size(size_str: str) -> int:
    """
    Accepts sizes like '100G' '500GB' etc. Simple parse for G/T.
    If disk record already contains 'size_bytes' return that.
    """
    if isinstance(size_str, int):
        return size_str
    s = str(size_str).upper().strip()
    if s.endswith('G'):
        return int(float(s[:-1]) * 1024**3)
    if s.endswith('GB'):
        return int(float(s[:-2]) * 1024**3)
    if s.endswith('T'):
        return int(float(s[:-1]) * 1024**4)
    if s.endswith('TB'):
        return int(float(s[:-2]) * 1024**4)
    try:
        return int(s)
    except:
        return 0

def _min_disk_bytes(disks: List[Dict[str,Any]]) -> int:
    sizes = []
    for d in disks:
        if d.get('size_bytes'):
            sizes.append(int(d['size_bytes']))
        else:
            sizes.append(parse_disk_size(d.get('size','0')))
    return min(sizes) if sizes else 0

def build_layout(disks: List[Dict[str,Any]], layout: str) -> Dict[str,Any]:
    """
    Returns:
    {
      "layout": "raidz1",
      "vdev_count": 1,
      "usable_capacity": "300G",
      "vdevs": [ ["/dev/sda","/dev/sdb","/dev/sdc"] ],
      "warnings": [...]
    }
    Supports layout: single, mirror, raidz1, raidz2, raidz3
    """
    if not disks:
        return {"error":"no disks provided"}

    n = len(disks)
    warnings = []
    min_bytes = _min_disk_bytes(disks)
    # convert to readable
    def _bytes_to_readable(b): return f"{int(b/1024**3)}G"

    if layout == 'single':
        # each disk as its own vdev (or single-disk pool)
        vdevs = [[d['devpath'] if d.get('devpath') else d.get('name')] for d in disks]
        usable = sum([min_bytes for _ in disks])
        return {"layout":"single","vdev_count":len(vdevs),"usable_capacity":_bytes_to_readable(min_bytes*len(vdevs)),"vdevs":vdevs,"warnings":warnings}

    if layout == 'mirror':
        # Mirror vdevs pair up as pairs
        if n % 2 != 0:
            warnings.append("odd number of disks for mirror — last vdev will be single")
        vdevs=[]
        for i in range(0,n,2):
            pair = []
            pair.append(disks[i].get('devpath') or disks[i].get('name'))
            if i+1 < n:
                pair.append(disks[i+1].get('devpath') or disks[i+1].get('name'))
            vdevs.append(pair)
        usable = min_bytes * len(vdevs)
        return {"layout":"mirror","vdev_count":len(vdevs),"usable_capacity":_bytes_to_readable(usable),"vdevs":vdevs,"warnings":warnings}

    # raidz families
    raidz_n = 0
    if layout == 'raidz1': raidz_n = 1
    if layout == 'raidz2': raidz_n = 2
    if layout == 'raidz3': raidz_n = 3

    if raidz_n > 0:
        # simple strategy: all disks into one vdev if count >= parity+1
        if n < raidz_n+1:
            warnings.append(f"not enough disks for {layout} (need >= {raidz_n+1})")
            # fallback: make single or mirror groups
        # pick vdev width = n
        vdevs = [[d.get('devpath') or d.get('name') for d in disks]]
        # usable = (n - parity) * min_disk_size
        usable = (n - raidz_n) * min_bytes if n > raidz_n else 0
        return {"layout": layout, "vdev_count": len(vdevs), "usable_capacity": _bytes_to_readable(usable), "vdevs": vdevs, "warnings": warnings}

    # fallback
    return {"error":"unknown layout"}

#new code---

def build_layout(level: str, disks: List[str], mirrors: int = 2, vdevs: int = 1) -> Dict[str, Any]:
    # normalize input (list of devpaths)
    ds = list(disks)
    if level == "single":
        return {"vdevs":[{"type":"single","disks":[d]} for d in ds]}

    if level == "mirror":
        if len(ds) % mirrors != 0:
            return {"error": f"{mirrors}-way mirror requires {mirrors} disks per vdev"}
        chunks = [ds[i:i+mirrors] for i in range(0,len(ds),mirrors)]
        return {"vdevs":[{"type":f"mirror-{mirrors}","disks":c} for c in chunks]}

    if level.startswith("raidz"):
        try:
            z = int(level[-1])
        except:
            return {"error":"invalid raidz level"}
        minreq = z + 2
        if len(ds) < minreq:
            return {"error":f"RAIDZ{z} needs at least {minreq} disks"}
        # split into vdevs (approx equal)
        per_vdev = max(minreq, len(ds)//vdevs)
        chunks = [ds[i:i+per_vdev] for i in range(0, len(ds), per_vdev)]
        return {"vdevs":[{"type":level,"disks":c} for c in chunks]}

    return {"error":"unknown level"}
    
#more new--- db --ke saath -- checkout
def build_layout(level, disks, mirrors=2, vdevs=1):
    if level == "single":
        return {"vdevs":[{"type":"single","disks":[d]} for d in disks]}

    if level == "mirror":
        if len(disks) % mirrors != 0:
            return {"error":"invalid mirror count"}
        chunks = [disks[i:i+mirrors] for i in range(0,len(disks),mirrors)]
        return {"vdevs":[{"type":"mirror","disks":c} for c in chunks]}

    if level.startswith("raidz"):
        z = int(level[-1])  # 1/2/3
        minreq = z+2
        if len(disks) < minreq:
            return {"error":f"RAIDZ{z} requires {minreq} disks"}
        return {"vdevs":[{"type":level,"disks":disks}]}

    return {"error":"invalid level"}    

