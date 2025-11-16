"""
backend/app/acl_manager.py
---------------------------
Unified ACL Manager for MyNAS.

Handles:
 - POSIX ACL operations (setfacl / getfacl)
 - High-level ACL operations (read/write/full)
 - Dataset ACL listing and modifications
 - Bridges backend.permissions (persistent ACL) with OS-level ACLs
"""

import os
import subprocess
import logging
from backend.app.permissions import (
    overwrite_acl_list,
    clear_acl,
    set_acl_record,
    delete_acl_record,
    list_acls as list_stored_acls,
)

logger = logging.getLogger("mynas.acl_manager")


# -------------------------------------------------------------------
# 🖥 POSIX ACL HELPERS (Linux setfacl)
# -------------------------------------------------------------------

def apply_posix_acl(path: str, username: str, permissions: str):
    """
    permissions: 'r', 'rw', 'rwx', etc.
    Applies POSIX ACL via setfacl
    """
    try:
        cmd = ["setfacl", "-m", f"user:{username}:{permissions}", path]
        subprocess.run(cmd, check=True)
        logger.info(f"POSIX ACL applied: {username}:{permissions} on {path}")
        return {"status": "ok", "path": path, "user": username, "permissions": permissions}
    except Exception as e:
        logger.error(f"POSIX ACL error: {e}")
        return {"status": "error", "error": str(e)}


def remove_posix_acl(path: str, username: str):
    """
    Removes POSIX ACL entry via setfacl
    """
    try:
        cmd = ["setfacl", "-x", f"user:{username}", path]
        subprocess.run(cmd, check=True)
        logger.info(f"POSIX ACL removed: {username} on {path}")
        return {"status": "removed", "path": path, "user": username}
    except Exception as e:
        logger.error(f"Error removing POSIX ACL: {e}")
        return {"status": "error", "error": str(e)}


# -------------------------------------------------------------------
# 🌐 HIGH-LEVEL ACL OPERATIONS (for datasets & backend.permissions)
# -------------------------------------------------------------------

def set_acl(path: str, username: str, permissions: str):
    """
    Unified method to set ACL entry for user on a path:
     - Persist in config (backend.permissions)
     - Apply to OS (POSIX ACL)
    """
    logger.debug(f"Setting ACL: {username} => {permissions} on {path}")

    # Persistent ACL
    result = set_acl_record(path, username, permissions)

    # POSIX ACL
    apply_posix_acl(path, username, permissions)

    return result


def remove_acl(path: str, username: str):
    """
    Unified method to remove ACL entry from:
     - Persistent config
     - OS filesystem ACL
    """
    logger.debug(f"Removing ACL for {username} on {path}")

    delete_acl_record(path, username)
    remove_posix_acl(path, username)

    return {"status": "deleted", "path": path, "user": username}


# -------------------------------------------------------------------
# 🧩 DATASET-LEVEL ACL OPERATIONS (Optional, future ZFS/NFS logic)
# -------------------------------------------------------------------

def set_dataset_acl(dataset: str, user: str, permission: str):
    """
    High-level ACL for datasets. Permission keywords:
      - "read"
      - "write"
      - "full"
    """
    logger.info(f"Dataset ACL => {dataset} : {user} = {permission}")

    perm_map = {
        "read": "r--",
        "write": "rw-",
        "full": "rwx"
    }

    posix_perm = perm_map.get(permission, "r--")
    return set_acl(dataset, user, posix_perm)


def remove_dataset_acl(dataset: str, user: str):
    logger.info(f"Removing dataset ACL => {dataset} : {user}")
    return remove_acl(dataset, user)


def list_dataset_acls(dataset: str):
    """Return ACL entries for only this dataset/path"""
    return [a for a in list_stored_acls() if a["path"] == dataset]


# -------------------------------------------------------------------
# 🧰 FULL ACL REWRITE API (Hooks into backend.permissions)
# -------------------------------------------------------------------

def rewrite_acl(path: str, acl_list):
    """
    Overwrite full ACL list for a path.
    Called from RPC setAcl().
    """
    logger.info(f"Rewriting ACL for {path}: {len(acl_list)} entries")

    # Persistent rewrite
    overwrite_acl_list(path, acl_list)

    # Apply POSIX ACL globally
    clear_posix(path)
    for entry in acl_list:
        apply_posix_acl(path, entry["username"], entry["permissions"])

    return {"status": "rewritten", "count": len(acl_list)}


def clear_posix(path: str):
    """
    Remove all POSIX ACLs for the path.
    """
    try:
        subprocess.run(["setfacl", "-b", path], check=True)
        logger.info(f"POSIX ACLs cleared for {path}")
    except:
        logger.warning(f"Could not clear POSIX ACL for {path}")


def clear_acl_all(path: str):
    """
    Clear full ACL for path:
     - Persistent config
     - POSIX ACL
    """
    clear_acl(path)
    clear_posix(path)
    return {"status": "cleared", "path": path}
