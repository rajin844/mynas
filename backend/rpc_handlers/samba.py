# backend/rpc_handlers/samba.py
from backend.storage.samba_manager import (
    list_smb_shares,
    add_smb_share,
    remove_smb_share
)

def rpc_list():
    return list_smb_shares()

def rpc_create(name: str, path: str, guest_ok: bool):
    return add_smb_share(name, path, guest_ok)

def rpc_delete(name: str):
    return remove_smb_share(name)

def register_rpc(register):
    register("samba", {
        "list": rpc_list,
        "create": rpc_create,
        "delete": rpc_delete,
    })
