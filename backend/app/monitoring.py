"""
Monitoring helpers for MyNAS backend
Provides CPU, RAM, Disk, and (optional ZFS) stats.
"""

import psutil

def cpu_info():
    """Returns current CPU usage %."""
    return psutil.cpu_percent(interval=0.1)

def ram_info():
    """Returns RAM usage stats."""
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "used": mem.used,
        "free": mem.available,
        "percent": mem.percent,
    }

def disk_info():
    """
    Returns info for ALL disks.
    IMPORTANT: no arguments — compatible with main.py
    """
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue  # skip restricted mounts

        disks.append({
            "device": part.device,
            "mount": part.mountpoint,
            "fstype": part.fstype,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
        })
    return disks
