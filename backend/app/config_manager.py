"""
backend/app/config_manager.py
-----------------------------
Central configuration manager for MyNAS.
Handles:
 - Safe read/write of config.json
 - Initialization on first boot
 - Automatic backups
 - Global access via get_config() / save_config()
"""

import threading
from typing import Any, Dict, List
from datetime import datetime
from pathlib import Path
import json
import shutil
import logging

logger = logging.getLogger("mynas.config")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"
BACKUP_DIR = CONFIG_DIR / "backups"

_lock = threading.Lock()


class ConfigManager:
    """Thread-safe JSON configuration database for MyNAS."""

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {}
        self.ensure_initialized()

    # -----------------------------------------------------------------------
    # 🧱 Initialization
    # -----------------------------------------------------------------------
    def ensure_initialized(self):
        """Ensure config.json exists and is valid."""
        if not CONFIG_FILE.exists():
            logger.info("No config.json found; initializing new configuration.")
            self.data = self._default_config()
            self._save_to_disk(self.data)
        else:
            self.reload()

    # -----------------------------------------------------------------------
    # 🧩 Core I/O
    # -----------------------------------------------------------------------
    def reload(self) -> Dict[str, Any]:
        """Reload config.json into memory."""
        with _lock:
            try:
                self.data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                logger.debug("Config reloaded successfully.")
            except Exception as e:
                logger.error(f"Error reading config.json: {e}")
                self.data = self._default_config()
                self._save_to_disk(self.data)
            return self.data

    def save(self, data: Dict[str, Any] = None):
        """Save the current (or provided) data to config.json and backup."""
        with _lock:
            if data is not None:
                self.data = data
            self._create_backup()
            self._save_to_disk(self.data)
            logger.info("Configuration saved successfully.")

    # -----------------------------------------------------------------------
    # 🧩 File Ops
    # -----------------------------------------------------------------------
    def _save_to_disk(self, data: Dict[str, Any]):
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _create_backup(self):
        if CONFIG_FILE.exists():
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            backup_file = BACKUP_DIR / f"config_{ts}.json"
            shutil.copy(CONFIG_FILE, backup_file)
            backups = sorted(BACKUP_DIR.glob("config_*.json"), reverse=True)
            for old in backups[10:]:
                try:
                    old.unlink()
                except Exception:
                    pass

    # -----------------------------------------------------------------------
    # 🧠 Section Getters/Setters
    # -----------------------------------------------------------------------
    def get_section(self, section: str) -> Any:
        """Return specific section dict."""
        return self.data.get(section, {})

    def set_section(self, section: str, value: Any):
        """Replace an entire section."""
        self.data[section] = value
        self.save()

    # -----------------------------------------------------------------------
    # 👤 User Management
    # -----------------------------------------------------------------------
    def list_users(self) -> List[Dict[str, Any]]:
        return self.data.get("users", [])

    def add_user(self, user_obj: Dict[str, Any]):
        users = self.data.setdefault("users", [])
        users.append(user_obj)
        self.save()

    def remove_user(self, username: str):
        users = [u for u in self.data.get("users", []) if u["username"] != username]
        self.data["users"] = users
        self.save()

    # -----------------------------------------------------------------------
    # 💾 Storage Management
    # -----------------------------------------------------------------------
    def get_storage(self):
        return self.data.get("storage", {"pools": [], "datasets": []})

    def update_storage(self, storage_data: Dict[str, Any]):
        self.data["storage"] = storage_data
        self.save()

    # -----------------------------------------------------------------------
    # 📂 Shares Management
    # -----------------------------------------------------------------------
    def list_shares(self):
        return self.data.get("shares", [])

    def add_share(self, share_obj: Dict[str, Any]):
        shares = self.data.setdefault("shares", [])
        shares.append(share_obj)
        self.save()

    def remove_share(self, name: str):
        shares = [s for s in self.data.get("shares", []) if s["name"] != name]
        self.data["shares"] = shares
        self.save()

    # -----------------------------------------------------------------------
    # 🔐 ACL Management
    # -----------------------------------------------------------------------
    def list_acls(self):
        return self.data.get("acl", [])

    def add_acl(self, acl_entry: Dict[str, Any]):
        acls = self.data.setdefault("acl", [])
        acls.append(acl_entry)
        self.save()

    def remove_acl(self, path: str, username: str):
        acls = [
            a
            for a in self.data.get("acl", [])
            if not (a["path"] == path and a["user"] == username)
        ]
        self.data["acl"] = acls
        self.save()

    # -----------------------------------------------------------------------
    # 🌐 Network Section
    # -----------------------------------------------------------------------
    def get_network(self):
        return self.data.get("network", {"interfaces": [], "dns": []})

    def update_network(self, new_data: Dict[str, Any]):
        self.data["network"] = new_data
        self.save()

    # -----------------------------------------------------------------------
    # 🔁 Backups
    # -----------------------------------------------------------------------
    def list_backups(self) -> List[str]:
        return sorted([b.name for b in BACKUP_DIR.glob("config_*.json")], reverse=True)

    def restore_backup(self, filename: str) -> bool:
        src = BACKUP_DIR / filename
        if not src.exists():
            logger.error(f"Backup not found: {filename}")
            return False
        shutil.copy(src, CONFIG_FILE)
        self.reload()
        logger.info(f"Config restored from backup: {filename}")
        return True

    # -----------------------------------------------------------------------
    # ⚙️ Default Config Structure
    # -----------------------------------------------------------------------
    def _default_config(self) -> Dict[str, Any]:
        return {
            "system": {
                "hostname": "mynas",
                "version": "1.0.0",
                "timezone": "UTC",
            },
            "users": [
                {"username": "admin", "role": "admin", "password": "admin"}
            ],
            "storage": {"pools": [], "datasets": []},
            "shares": [],
            "acl": [],
            "network": {"interfaces": [], "dns": []},
            "backups": [],
        }


# ---------------------------------------------------------------------------
# ✅ Global instance and utility functions
# ---------------------------------------------------------------------------

_cfg = ConfigManager()


def get_config() -> Dict[str, Any]:
    """Return full config dictionary (auto-reloads)."""
    return _cfg.reload()


def save_config(data: Dict[str, Any]) -> None:
    """Save provided config dict to disk (creates backup)."""
    _cfg.save(data)


def ensure_config_ready():
    """Ensure config is initialized at startup."""
    _cfg.ensure_initialized()


# Expose instance for direct use (optional)
cfg = _cfg
