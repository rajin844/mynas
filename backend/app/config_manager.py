"""
backend/app/config_manager.py
-----------------------------
Enhanced configuration manager for MyNAS.

✔ Thread-safe JSON config DB
✔ Auto-backup (10 versions)
✔ Dirty-modules tracking
✔ Storage / Pools / Datasets support
✔ ACL & Shares management
✔ Users & Groups support
✔ Network section support
✔ Snapshot & Tasks ready
✔ Global utility helpers
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


# =======================================================================
#  MAIN CLASS
# =======================================================================
class ConfigManager:
    """Thread-safe JSON configuration database for MyNAS."""

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {}
        self.ensure_initialized()

    # -------------------------------------------------------------------
    # 🧱 Initialization
    # -------------------------------------------------------------------
    def ensure_initialized(self):
        """Ensure config.json exists and contains valid JSON."""
        if not CONFIG_FILE.exists():
            logger.info("config.json missing → creating new default configuration.")
            self.data = self._default_config()
            self._save_to_disk(self.data)
        else:
            self.reload()

    # -------------------------------------------------------------------
    # 🔁 Reload
    # -------------------------------------------------------------------
    def reload(self) -> Dict[str, Any]:
        """Reload config.json into memory safely."""
        with _lock:
            try:
                text = CONFIG_FILE.read_text(encoding="utf-8").strip()
                if not text:
                    raise ValueError("config.json is empty")

                self.data = json.loads(text)

                # Ensure missing sections (compatibility with older versions)
                self._ensure_integrity()

                logger.debug("Config reloaded")
            except Exception as e:
                logger.error(f"Error reading config.json — restoring defaults: {e}")
                self.data = self._default_config()
                self._save_to_disk(self.data)

            return self.data

    # -------------------------------------------------------------------
    # 💾 Save
    # -------------------------------------------------------------------
    def save(self, data: Dict[str, Any] = None):
        """Save full config to disk (with backup)."""
        with _lock:
            if data is not None:
                self.data = data

            self._create_backup()
            self._save_to_disk(self.data)

            logger.info("Configuration saved successfully.")

    # -------------------------------------------------------------------
    # 💾 Save to disk
    # -------------------------------------------------------------------
    def _save_to_disk(self, data: Dict[str, Any]):
        CONFIG_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # -------------------------------------------------------------------
    # 🗄️ Backup Rotation
    # -------------------------------------------------------------------
    def _create_backup(self):
        if CONFIG_FILE.exists():
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            backup = BACKUP_DIR / f"config_{ts}.json"
            shutil.copy(CONFIG_FILE, backup)

            # keep latest 10 backups
            backups = sorted(BACKUP_DIR.glob("config_*.json"), reverse=True)
            for old in backups[10:]:
                try: old.unlink()
                except: pass

    # ===================================================================
    #  GETTERS / SETTERS
    # ===================================================================

    def get_section(self, section: str) -> Any:
        return self.data.get(section, {})

    def set_section(self, section: str, value: Any):
        self.data[section] = value
        self.save()

    # -------------------------------------------------------------------
    # USER MANAGEMENT
    # -------------------------------------------------------------------
    def list_users(self) -> List[Dict[str, Any]]:
        return self.data.get("users", [])

    def add_user(self, obj: Dict[str, Any]):
        users = self.data.setdefault("users", [])
        users.append(obj)
        self.save()

    def remove_user(self, username: str):
        self.data["users"] = [
            u for u in self.data.get("users", []) if u["username"] != username
        ]
        self.save()

    # -------------------------------------------------------------------
    # STORAGE MANAGEMENT
    # -------------------------------------------------------------------
    def get_storage(self) -> Dict[str, Any]:
        return self.data.get("storage", {"pools": [], "datasets": []})

    def update_storage(self, storage_data: Dict[str, Any]):
        self.data["storage"] = storage_data
        self.save()

    # -------------------------------------------------------------------
    # SHARES
    # -------------------------------------------------------------------
    def list_shares(self):
        return self.data.get("shares", [])

    def add_share(self, obj: Dict[str, Any]):
        self.data.setdefault("shares", []).append(obj)
        self.save()

    def remove_share(self, name: str):
        self.data["shares"] = [s for s in self.data.get("shares", []) if s["name"] != name]
        self.save()

    # -------------------------------------------------------------------
    # ACL
    # -------------------------------------------------------------------
    def list_acls(self):
        return self.data.get("acl", [])

    def add_acl(self, entry: Dict[str, Any]):
        self.data.setdefault("acl", []).append(entry)
        self.save()

    def remove_acl(self, path: str, username: str):
        self.data["acl"] = [
            a for a in self.data.get("acl", [])
            if not (a["path"] == path and a["user"] == username)
        ]
        self.save()

    # -------------------------------------------------------------------
    # NETWORK
    # -------------------------------------------------------------------
    def get_network(self):
        return self.data.get("network", {"interfaces": [], "dns": []})

    def update_network(self, new_data: Dict[str, Any]):
        self.data["network"] = new_data
        self.save()

    # -------------------------------------------------------------------
    # TASKS SUPPORT (CRONJOBS)
    # -------------------------------------------------------------------
    def list_tasks(self):
        return self.data.get("tasks", [])

    def add_task(self, task_obj):
        self.data.setdefault("tasks", []).append(task_obj)
        self.save()

    # -------------------------------------------------------------------
    # SNAPSHOTS SUPPORT
    # -------------------------------------------------------------------
    def list_snapshots(self):
        return self.data.get("snapshots", [])

    def add_snapshot(self, snap):
        self.data.setdefault("snapshots", []).append(snap)
        self.save()

    # -------------------------------------------------------------------
    # DIRTY MODULES (AUTO-REFRESH)
    # -------------------------------------------------------------------
    def list_dirty(self):
        return self.data.get("dirty_modules", [])

    def mark_dirty(self, module: str):
        dirty = self.data.setdefault("dirty_modules", [])
        if module not in dirty:
            dirty.append(module)
            self.save()

    # ===================================================================
    #  DEFAULT CONFIG (EXPANDED)
    # ===================================================================
    def _default_config(self) -> Dict[str, Any]:
        return {
            "system": {
                "hostname": "mynas",
                "version": "1.0.0",
                "timezone": "UTC",
            },
            "dirty_modules": [],
            "users": [
                {"username": "admin", "role": "admin", "password": "admin"}
            ],
            "storage": {
                "pools": [],
                "datasets": [],
            },
            "shares": [],
            "acl": [],
            "network": {"interfaces": [], "dns": []},
            "tasks": [],
            "snapshots": [],
            "backups": [],
        }

    # -------------------------------------------------------------------
    # INTERNAL - Ensure missing sections exist
    # -------------------------------------------------------------------
    def _ensure_integrity(self):
        defaults = self._default_config()
        for key, default_value in defaults.items():
            if key not in self.data:
                self.data[key] = default_value
        # Do not save automatically during reload (avoids IO loop)


# ---------------------------------------------------------------------------
# GLOBAL HELPERS
# ---------------------------------------------------------------------------

_cfg = ConfigManager()

def load_config() -> Dict[str, Any]:
    return _cfg.reload()

def get_config() -> Dict[str, Any]:
    return _cfg.reload()

def save_config(d: Dict[str, Any]):
    return _cfg.save(d)

def ensure_config_ready():
    return _cfg.ensure_initialized()

def mark_dirty(module):
    return _cfg.mark_dirty(module)

# Expose instance for direct use
cfg = _cfg
