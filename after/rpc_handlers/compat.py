# backend/rpc_handlers/compat.py
import logging
logger = logging.getLogger("mynas.rpc.compat")
def rpc_ping(): return {"pong": True}
def register_rpc(register): register("compat", {"ping": rpc_ping})
