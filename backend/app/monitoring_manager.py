# backend/system/monitoring_manager.py
import psutil, time
from backend.drivers.driver_loader import get_driver
driver = get_driver()

def get_system_metrics():
    return {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "network": {"upload_bps": 0, "download_bps": 0}
    }

def get_cpu_usage(): return psutil.cpu_percent()
def get_memory_usage(): return psutil.virtual_memory().percent
def get_disk_usage(): return psutil.disk_usage("/").percent
def get_network_usage(): return {"upload_bps":0,"download_bps":0}
