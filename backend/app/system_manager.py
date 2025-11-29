"""
backend/system/system_manager.py
--------------------------------
System manager for MyNAS.
Provides:
 - Hostname operations
 - Timezone get/set
 - System reboot/shutdown
 - Kernel/system details
 - Uptime
 - Load averages
 - Package update status (Linux)
 - CPU / RAM info (basic)
"""

import asyncio
import platform
import psutil
import socket
import subprocess
import time
from datetime import datetime
from backend.app.safe_exec import safe_exec


# =====================================================================
# 🖥️ BASIC SYSTEM INFORMATION
# =====================================================================

async def get_hostname() -> str:
    return platform.node()


async def set_hostname(name: str) -> bool:
    """
    Set system hostname (Linux).
    Requires root.
    """
    cmd = ["hostnamectl", "set-hostname", name]
    ok, out, err = await safe_exec(cmd)

    return ok


# =====================================================================
# 🌐 NETWORK INFO
# =====================================================================

async def get_local_ip() -> str:
    """Get LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


# =====================================================================
# 🕒 TIME / TIMEZONE
# =====================================================================

async def get_timezone() -> str:
    ok, out, _ = await safe_exec(["timedatectl"])
    if not ok:
        return "Unknown"

    for line in out.splitlines():
        if "Time zone" in line:
            return line.split(":", 1)[1].strip().split(" ")[0]

    return "Unknown"


async def set_timezone(tz: str) -> bool:
    ok, _, _ = await safe_exec(["timedatectl", "set-timezone", tz])
    return ok


# =====================================================================
# 📦 PACKAGE MANAGER (OS UPDATE STATUS)
# =====================================================================

async def get_update_status() -> dict:
    """
    Check update availability (Debian/Ubuntu systems).
    """
    ok, out, err = await safe_exec(["apt", "list", "--upgradeable"])
    if not ok:
        return {"supported": False, "updates": []}

    updates = []
    for line in out.splitlines():
        if "upgradeable" in line:
            pkg = line.split("/", 1)[0]
            updates.append(pkg)

    return {
        "supported": True,
        "count": len(updates),
        "updates": updates
    }


# =====================================================================
# 🧠 SYSTEM SPECS (CPU / RAM)
# =====================================================================

async def get_cpu_info() -> dict:
    return {
        "model": platform.processor(),
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "freq": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        "load_avg": list(psutil.getloadavg()),
    }


async def get_ram_info() -> dict:
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "used": mem.used,
        "percent": mem.percent,
    }


# =====================================================================
# 🕒 UPTIME
# =====================================================================

async def get_uptime() -> str:
    boot_ts = psutil.boot_time()
    delta = time.time() - boot_ts
    return str(datetime.utcfromtimestamp(delta).strftime("%H:%M:%S"))


# =====================================================================
# 🔧 SYSTEM ACTIONS
# =====================================================================

async def system_reboot() -> bool:
    return (await safe_exec(["systemctl", "reboot"]))[0]


async def system_shutdown() -> bool:
    return (await safe_exec(["systemctl", "poweroff"]))[0]


# =====================================================================
# 📦 FULL SYSTEM SUMMARY (for dashboard)
# =====================================================================

async def system_summary() -> dict:
    return {
        "hostname": await get_hostname(),
        "ip": await get_local_ip(),
        "timezone": await get_timezone(),
        "uptime": await get_uptime(),
        "cpu": await get_cpu_info(),
        "ram": await get_ram_info(),
        "updates": await get_update_status(),
        "kernel": platform.release(),
        "platform": platform.system(),
    }
