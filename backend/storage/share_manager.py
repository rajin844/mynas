"""
backend/storage/share_manager.py
--------------------------------
Handles SMB/NFS shares for MyNAS.
Integrates with config_manager and WebSocket system.
"""

import logging
from backend.app.config_manager import ConfigManager
from backend.realtime.websocket_server import WSManagerProxy

cfg = ConfigManager()
logger = logging.getLogger("mynas.share_manager")

# -------------------------------------------------------------------
# 📦 Load and Sync Shares
# -------------------------------------------------------------------

def load_shares():
    """
    Loads existing shares from config.json.
    This is used during startup (called in app.main).
    Ensures that shares section exists and broadcasts to WS.
    """
    shares = cfg.list_shares()
    if shares is None:
        cfg.set_section("shares", [])
        shares = []
    logger.info(f"Loaded {len(shares)} shares from config.")
    WSManagerProxy.broadcast({"event": "shares_loaded", "count": len(shares)})
    return shares


# -------------------------------------------------------------------
# 📋 List Shares
# -------------------------------------------------------------------

def list_shares():
    """Return current shares from config.json."""
    return cfg.list_shares()


# -------------------------------------------------------------------
# ➕ Add Share
# -------------------------------------------------------------------

def add_share(name: str, path: str, protocol: str = "smb", readonly: bool = False, comment: str = ""):
    """
    Adds a new SMB/NFS share entry to config.
    - name: Share name
    - path: Filesystem path (e.g. /mnt/tank/media)
    - protocol: smb | nfs
    """
    new_share = {
        "name": name,
        "path": path,
        "protocol": protocol,
        "readonly": readonly,
        "comment": comment,
        "enabled": True,
    }

    existing = cfg.list_shares()
    # Avoid duplicates
    if any(s["name"] == name for s in existing):
        logger.warning(f"Share {name} already exists, skipping.")
        return {"status": "exists", "share": name}

    cfg.add_share(new_share)
    logger.info(f"Added new share: {name} ({protocol})")
    WSManagerProxy.broadcast({"event": "share_created", "share": new_share})
    return {"status": "created", "share": name}


# -------------------------------------------------------------------
# ❌ Remove Share
# -------------------------------------------------------------------

def remove_share(name: str):
    """Remove share by name."""
    shares = cfg.list_shares()
    if not any(s["name"] == name for s in shares):
        logger.warning(f"Share {name} not found.")
        return {"status": "not_found", "share": name}

    cfg.remove_share(name)
    logger.info(f"Removed share: {name}")
    WSManagerProxy.broadcast({"event": "share_removed", "share": name})
    return {"status": "deleted", "share": name}


# -------------------------------------------------------------------
# ⚙️ Modify Share
# -------------------------------------------------------------------

def update_share(name: str, updates: dict):
    """Modify an existing share by name."""
    shares = cfg.list_shares()
    updated = False
    for s in shares:
        if s["name"] == name:
            s.update(updates)
            updated = True
            break
    if updated:
        cfg.set_section("shares", shares)
        WSManagerProxy.broadcast({"event": "share_updated", "share": name, "changes": updates})
        logger.info(f"Updated share {name}: {updates}")
        return {"status": "updated", "share": name}
    else:
        logger.warning(f"Share {name} not found for update.")
        return {"status": "not_found", "share": name}


# -------------------------------------------------------------------
# 🔁 Sync with system (optional)
# -------------------------------------------------------------------

def sync_shares_with_system():
    """
    Placeholder for integrating with Samba/NFS config.
    This can be extended later to:
    - Rewrite /etc/samba/smb.conf or /etc/exports
    - Restart related daemons
    """
    shares = cfg.list_shares()
    logger.info(f"Synchronizing {len(shares)} shares with system services...")
    # TODO: call app.utils.smb_nfs_ops helpers here
    WSManagerProxy.broadcast({"event": "shares_sync", "count": len(shares)})
    return {"status": "synced", "shares": len(shares)}

