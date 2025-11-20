# backend/rpc_handlers/network.py
from backend.network.network_manager import get_network_interfaces, apply_network_settings , update_network , restart_network
import logging
logger = logging.getLogger("mynas.rpc.network")


def rpc_list_interfaces():
    return get_network_interfaces()

def rpc_apply(settings):
    return apply_network_settings(settings)

def register_rpc(register):
    register("network", {"listinterfaces": rpc_list_interfaces, "apply": rpc_apply})

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
