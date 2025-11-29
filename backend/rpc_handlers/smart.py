# backend/rpc_handlers/smart.py
from backend.storage.smart_manager import smart_scan_all

async def rpc_scan():
    return await smart_scan_all()

def register_rpc(register):
    register("smart", {"scan": rpc_scan})
