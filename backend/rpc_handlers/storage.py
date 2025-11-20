# backend/rpc_handlers/storage.py
import logging
logger = logging.getLogger("mynas.rpc.storage")
from backend.storage.storage_manager import list_disks, detect_disks, smart_health, disk_usage, get_storage_summary

def rpc_list_disks():
    return list_disks()

def rpc_detect():
    return detect_disks()

def rpc_smart(dev: str):
    return smart_health(dev)

def rpc_disk_usage(dev: str):
    return disk_usage(dev)

def rpc_summary():
    return get_storage_summary()

def register_rpc(register):
    register("storage", {
        "list_disks": rpc_list_disks,
        "detect": rpc_detect,
        "smart_info": rpc_smart,
        "disk_usage": rpc_disk_usage,
        "summary": rpc_summary,
    })
