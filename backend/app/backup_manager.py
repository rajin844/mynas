"""
backend/app/backup_manager.py
-----------------------------
Handles configuration and data backups for MyNAS.

Supports:
 - Listing config backups
 - Creating new config backups
 - Restoring from a backup
 - Deleting old backups
 - Optional rsync job for remote storage
 - WebSocket broadcast notifications
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional
from backend.app.config_manager import ConfigManager

# -------------------------------------------------------------------
# 📂 Paths
# -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
BACKUP_DIR = CONFIG_DIR / "backups"

# Ensure directories exist
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Singleton ConfigManager instance
cfg = ConfigManager()

# -------------------------------------------------------------------
# 📜 List Backups
# -------------------------------------------------------------------
def list_backups() -> List[str]:
    """Return sorted list of available config backup filenames."""
    files = sorted(BACKUP_DIR.glob("config_*.json"), reverse=True)
    return [f.name for f in files]


# -------------------------------------------------------------------
# 💾 Create Config Backup
# -------------------------------------------------------------------
def create_config_backup() -> Optional[str]:
    """
    Creates a timestamped config backup.
    Returns the new filename, or None if config missing.
    """
    config_file = CONFIG_DIR / "config.json"
    if not config_file.exists():
        return None

    # Force save to generate new backup
    cfg.save(cfg.data)
    files = list_backups()
    if files:
        _try_broadcast({"module": "backup", "action": "create", "file": files[0]})
        return files[0]
    return None


# -------------------------------------------------------------------
# 🔁 Restore Config Backup
# -------------------------------------------------------------------
def restore_config_backup(filename: str) -> bool:
    """
    Restore a configuration file from backup.
    """
    src = BACKUP_DIR / filename
    dst = CONFIG_DIR / "config.json"
    if not src.exists():
        return False

    shutil.copy(src, dst)
    _try_broadcast({"module": "backup", "action": "restore", "file": filename})
    return True


# -------------------------------------------------------------------
# ❌ Delete Config Backup
# -------------------------------------------------------------------
def delete_config_backup(filename: str) -> bool:
    """
    Delete a specific backup file.
    Returns True if deleted, False if not found or error.
    """
    target = BACKUP_DIR / filename
    if not target.exists():
        return False
    try:
        target.unlink()
        _try_broadcast({"module": "backup", "action": "delete", "file": filename})
        return True
    except Exception:
        return False


# -------------------------------------------------------------------
# 🌐 Rsync Backup (remote sync)
# -------------------------------------------------------------------
def run_rsync_backup(source: str, destination: str) -> bool:
    """
    Perform an rsync backup from source to destination directory.
    Example:
        run_rsync_backup('/mnt/tank/media/', '/mnt/backup/media/')
    """
    try:
        subprocess.check_call(["rsync", "-a", source, destination])
        _try_broadcast(
            {
                "module": "backup",
                "action": "rsync",
                "source": source,
                "destination": destination,
            }
        )
        return True
    except Exception:
        return False


# -------------------------------------------------------------------
# 📡 WebSocket Broadcast Helper
# -------------------------------------------------------------------
def _try_broadcast(msg: dict):
    """Try to broadcast a message over WebSocket if available."""
    try:
        from app.realtime.websocket_server import WSManagerProxy
        WSManagerProxy.broadcast(msg)
    except Exception:
        pass
