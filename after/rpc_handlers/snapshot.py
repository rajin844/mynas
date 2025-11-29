# backend/rpc_handlers/shares.py
import logging
logger = logging.getLogger("mynas.rpc.shares")

from backend.storage.share_manager import (
    list_shares,
    create_smb_share,
    create_nfs_share,
    remove_share,
    smb_status,
    nfs_status,
)

def rpc_list():
    return list_shares()

def rpc_smb_create(name: str, path: str, options: dict = None):
    return create_smb_share(name, path, options or {})

def rpc_nfs_create(name: str, path: str, options: dict = None):
    return create_nfs_share(name, path, options or {})

def rpc_delete(uuid: str):
    return remove_share(uuid)

def rpc_smb_status():
    return smb_status()

def rpc_nfs_status():
    return nfs_status()


def register_rpc(register):
    register("shares", {
        "list": rpc_list,
        "smb_create": rpc_smb_create,
        "nfs_create": rpc_nfs_create,
        "delete": rpc_delete,
        "smb_status": rpc_smb_status,
        "nfs_status": rpc_nfs_status,
    })
