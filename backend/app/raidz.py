# backend/app/raidz.py
"""
RAIDZ Layout Builder (TrueNAS style)
Produces parity layout for raidz1/2/3 or single parity.
"""

def build_raidz_layout(devices, level="raidz1"):
    level_map = {
        "single": 1,
        "raidz1": 1,
        "raidz2": 2,
        "raidz3": 3,
    }

    if level not in level_map:
        raise ValueError("Invalid RAIDZ level")

    parity = level_map[level]
    d = len(devices)

    if d <= parity:
        raise ValueError(f"{level} requires at least {parity + 1} devices")

    return {
        "level": level,
        "parity": parity,
        "total": d,
        "data_disks": d - parity,
        "usable_ratio": round((d - parity) / d, 3),
        "vdev": devices,
    }
