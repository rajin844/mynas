# backend/rpc_handlers/smart.py
import subprocess
import re

def smart_info(device: str):
    """
    Run smartctl for given disk.
    device: "/dev/sda", "/dev/sdb", "/dev/nvme0"
    """
    try:
        output = subprocess.check_output(
            ["smartctl", "-a", device],
            stderr=subprocess.STDOUT,
            text=True
        )
    except Exception as e:
        return {"error": f"smartctl failed: {e}"}

    info = {
        "device": device,
        "model": None,
        "serial": None,
        "firmware": None,
        "temp": None,
        "power_on_hours": None,
        "reallocated": None,
        "pending": None,
        "healthy": None
    }

    # Parse model
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
    if m: info["temp"] = int(m.group(1))

    # Power-on hours
    m = re.search(r"Power_On_Hours.*?(\d+)", output)
    if m: info["power_on_hours"] = int(m.group(1))

    # Reallocated sectors
    m = re.search(r"Reallocated_Sector_Ct.*?(\d+)", output)
    if m: info["reallocated"] = int(m.group(1))

    # Pending sectors
    m = re.search(r"Current_Pending_Sector.*?(\d+)", output)
    if m: info["pending"] = int(m.group(1))

    # Health status
    if "SMART overall-health self-assessment test result" in output:
        healthy = "PASSED" in output
        info["healthy"] = healthy

    return info


def register_rpc(register):
    register("smart", {
        "info": smart_info,
    })
