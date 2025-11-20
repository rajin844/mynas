# backend/rpc_handlers/system.py
import platform, os, logging
logger = logging.getLogger("mynas.rpc.system")

def rpc_info():
    return {"hostname": platform.node(), "os": platform.platform(), "cpu": os.cpu_count()}

def rpc_hardware():
    # lightweight hardware summary
    try:
        return {"mem_total": None, "disks": []}
    except Exception as e:
        logger.exception(e); return {"error": str(e)}

def rpc_info():
    return system_info()

def rpc_reboot():
    return reboot()

def rpc_shutdown():
    return shutdown()
def register_rpc(register):
    register("system", {"info": rpc_info, "reboot": rpc_reboot, "shutdown": rpc_shutdown})

def register_rpc(register):
    register("system", {"info": rpc_info, "hardware": rpc_hardware})
