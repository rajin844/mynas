# backend/rpc_handlers/raidz.py
"""
RAIDZ Builder RPC
Generates optimal RAIDZ vdev layout from disk list.
"""

import math

def build_raidz(devices, raidz_level="single"):
    """
    devices = ["/dev/sda", "/dev/sdb", ...]
    raidz_level = "single" | "raidz1" | "raidz2" | "raidz3"
    """
    if not devices or len(devices) < 2:
        raise ValueError("At least 2 disks required for RAIDZ")

    level_map = {
        "single": 1,
        "raidz1": 1,
        "raidz2": 2,
        "raidz3": 3,
    }

    parity = level_map.get(raidz_level, 1)

    d = len(devices)
    if d <= parity:
        raise ValueError(f"RAIDZ{parity} requires at least {parity + 1} disks")

    return {
        "raidz_level": f"raidz{parity}",
        "parity": parity,
        "total_disks": d,
        "data_disks": d - parity,
        "vdev": devices,
        "usable_capacity_ratio": (d - parity) / d
    }

def register_rpc(register):
    register("raidz", {
        "build": build_raidz,
    })
