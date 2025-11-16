# backend/rpc_handlers/network.py
import logging
logger = logging.getLogger("mynas.rpc.network")

from backend.app.network_manager import (
    get_interfaces,
    update_network,
    restart_network,
)

def rpc_list_interfaces():
    return get_interfaces()

def rpc_update(config: dict):
    return update_network(config)

def rpc_restart():
    return restart_network()

def register_rpc(register):
    register("network", {
        "list_interfaces": rpc_list_interfaces,
        "update": rpc_update,
        "restart": rpc_restart,
    })
