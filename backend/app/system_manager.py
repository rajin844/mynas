# backend/system/system_manager.py
import platform
import os

def system_info():
    return {
        "os": platform.platform(),
        "kernel": platform.release(),
        "hostname": platform.node(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }

def reboot():
    os.system("reboot")
    return {"status": "rebooting"}

def shutdown():
    os.system("shutdown -h now")
    return {"status": "shutdown"}
    
system_manager = SystemManager()    
