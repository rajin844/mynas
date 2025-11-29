"""
backend/rpc_handlers/system.py
------------------------------
RPC handler for system-level operations.
Backed by system_manager.py
"""

import logging
logger = logging.getLogger("mynas.rpc.system")

from backend.system.system_manager import (
    system_summary,
    get_hostname,
    set_hostname,
    get_timezone,
    set_timezone,
    system_reboot,
    system_shutdown,
)

# ===========================================================
# RPC METHODS
# ===========================================================

async def rpc_summary():
    return await system_summary()

async def rpc_get_hostname():
    return await get_hostname()

async def rpc_set_hostname(hostname: str):
    return await set_hostname(hostname)

async def rpc_get_timezone():
    return await get_timezone()

async def rpc_set_timezone(timezone: str):
    return await set_timezone(timezone)

async def rpc_reboot():
    return await system_reboot()

async def rpc_shutdown():
    return await system_shutdown()


# ===========================================================
# REGISTER SERVICE
# ===========================================================

def register_rpc(register):
    """
    register("SYSTEM", {...})
    """
    register("SYSTEM", {
        "summary": rpc_summary,
        "getHostname": rpc_get_hostname,
        "setHostname": rpc_set_hostname,
        "getTimezone": rpc_get_timezone,
        "setTimezone": rpc_set_timezone,
        "reboot": rpc_reboot,
        "shutdown": rpc_shutdown,
    })

    logger.info("SYSTEM RPC registered")
