# backend/app/system_manager.py
"""
System-wide utilities for MyNAS
- Hostname
- Timezone
- System info
- Reboot / shutdown
- Uptime
"""

import os
import subprocess
import platform
import psutil
import time
from datetime import datetime
from pathlib import Path


def _run(cmd):
    """Run system command safely."""
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)


# ---------------------------------------------------
# SYSTEM INFO
# ---------------------------------------------------

def system_info():
    """Return complete NAS system info"""
    return {
        "hostname": platform.node(),
        "os": platform.platform(),
        "kernel": platform.release(),
        "cpu": {
            "model": _cpu_model(),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
        },
        "memory": {
            "total": psutil.virtual_memory().total,
            "used": psutil.virtual_memory().used,
            "free": psutil.virtual_memory().available,
        },
        "uptime": uptime(),
        "time": datetime.now().isoformat(),
    }


def _cpu_model():
    try:
        if Path("/proc/cpuinfo").exists():
            for line in open("/proc/cpuinfo"):
                if "model name" in line.lower():
                    return line.split(":")[1].strip()
    except:
        pass
    return platform.processor()


# ---------------------------------------------------
# HOSTNAME
# ---------------------------------------------------

def get_hostname():
    return platform.node()


def set_hostname(new_name: str):
    if not new_name:
        raise ValueError("Hostname cannot be empty")

    _run(["hostnamectl", "set-hostname", new_name])
    return {"status": "ok", "hostname": new_name}


# ---------------------------------------------------
# TIMEZONE
# ---------------------------------------------------

def get_timezone():
    try:
        zone = _run(["timedatectl"])
        for line in zone.splitlines():
            if "Time zone:" in line:
                return line.split(":")[1].strip()
    except:
        pass
    return "UTC"


def set_timezone(tz: str):
    if not tz:
        raise ValueError("Timezone cannot be empty")

    _run(["timedatectl", "set-timezone", tz])
    return {"status": "ok", "timezone": tz}


# ---------------------------------------------------
# SYSTEM POWER CONTROL
# ---------------------------------------------------

def reboot():
    _run(["systemctl", "reboot"])
    return {"status": "rebooting"}


def shutdown():
    _run(["systemctl", "poweroff"])
    return {"status": "shutting_down"}


# ---------------------------------------------------
# UPTIME
# ---------------------------------------------------

def uptime():
    seconds = time.time() - psutil.boot_time()
    return int(seconds)
