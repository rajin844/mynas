# backend/app/smart.py
"""
SMART health parser using smartctl
"""

import subprocess
import re

def run(cmd):
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)

def smart_health(device: str):
    try:
        output = run(["smartctl", "-a", device])
    except Exception as e:
        return {"error": f"SMART query failed: {e}"}

    info = {
        "device": device,
        "model": None,
        "serial": None,
        "firmware": None,
        "temperature": None,
        "power_on_hours": None,
        "reallocated_sectors": None,
        "pending_sectors": None,
        "healthy": None,
        "raw": output,
    }

    # Model
    m = re.search(r"Model Family:\s+(.+)", output)
    if m: info["model"] = m.group(1).strip()

    # Serial
    m = re.search(r"Serial Number:\s+(.+)", output)
    if m: info["serial"] = m.group(1).strip()

    # Firmware
    m = re.search(r"Firmware Version:\s+(.+)", output)
    if m: info["firmware"] = m.group(1).strip()

    # Temperature
    m = re.search(r"Temperature_Celsius.*?(\d+)", output)
    if m: info["temperature"] = int(m.group(1))

    # POH
    m = re.search(r"Power_On_Hours.*?(\d+)", output)
    if m: info["power_on_hours"] = int(m.group(1))

    # Reallocated
    m = re.search(r"Reallocated_Sector_Ct.*?(\d+)", output)
    if m: info["reallocated_sectors"] = int(m.group(1))

    # Pending
    m = re.search(r"Current_Pending_Sector.*?(\d+)", output)
    if m: info["pending_sectors"] = int(m.group(1))

    # Health verdict
    if "SMART overall-health" in output:
        info["healthy"] = "PASSED" in output

    return info
