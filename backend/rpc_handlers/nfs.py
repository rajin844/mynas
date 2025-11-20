# backend/rpc_handlers/shares.py
import logging
logger = logging.getLogger("mynas.rpc.shares")
from backend.storage.share_manager import list_shares, create_share, delete_share, smb_status, nfs_status

def rpc_list(): return list_shares()
def rpc_create(name: str, path: str, protocol: str, options: dict = None): return create_share(name, path, protocol, options or {})
def rpc_delete(uuid: str): return delete_share(uuid)
def rpc_smb_status(): return smb_status()
def rpc_nfs_status(): return nfs_status()

def register_rpc(register):
    register("shares", {"list": rpc_list, "create": rpc_create, "delete": rpc_delete, "smb_status": rpc_smb_status, "nfs_status": rpc_nfs_status})
