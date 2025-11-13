"""
backend/app/permissions.py
--------------------------
ACL (Access Control List) and permission logic for MyNAS.

Supports:
 - Setting, listing, deleting ACL entries
 - Persistent storage via config_manager
 - Optional OS-level application via setfacl (future)
"""

import logging
from backend.app.config_manager import ConfigManager
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.permissions")


# -------------------------------------------------------------------
# 📋 List ACLs
# -------------------------------------------------------------------

def list_acls():
    """Return list of ACL entries from config.json"""
    acls = cfg.list_acls()
    logger.debug(f"Listing {len(acls)} ACL entries.")
    return acls


# -------------------------------------------------------------------
# ➕ Set / Update ACL
# -------------------------------------------------------------------

def set_acl_record(path: str, username: str, permissions: str):
    """
    Create or update an ACL entry.
    :param path: Target filesystem path
    :param username: User to apply ACL
    :param permissions: String (e.g. rwx, r--, etc.)
    """
    acls = cfg.list_acls()

    # Check if ACL exists
    updated = False
    for acl in acls:
        if acl["path"] == path and acl["user"] == username:
            acl["permissions"] = permissions
            updated = True
            break

    if not updated:
        new_acl = {"path": path, "user": username, "permissions": permissions}
        acls.append(new_acl)
        logger.info(f"New ACL created: {new_acl}")
        WSManagerProxy.broadcast({"event": "acl_created", "acl": new_acl})
    else:
        logger.info(f"ACL updated for {username} on {path}")
        WSManagerProxy.broadcast({
            "event": "acl_updated",
            "user": username,
            "path": path,
            "permissions": permissions
        })

    cfg.set_section("acl", acls)
    return {"status": "updated" if updated else "created", "user": username, "path": path}


# -------------------------------------------------------------------
# ❌ Delete ACL
# -------------------------------------------------------------------

def delete_acl_record(path: str, username: str):
    """
    Remove ACL record for given path and user.
    """
    acls = cfg.list_acls()
    before = len(acls)
    new_acls = [a for a in acls if not (a["path"] == path and a["user"] == username)]
    removed = before != len(new_acls)

    cfg.set_section("acl", new_acls)

    if removed:
        logger.info(f"ACL removed for {username} on {path}")
        WSManagerProxy.broadcast({"event": "acl_deleted", "user": username, "path": path})
        return {"status": "deleted", "user": username, "path": path}
    else:
        logger.warning(f"No ACL found for {username} on {path}")
        return {"status": "not_found", "user": username, "path": path}
