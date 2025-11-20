# backend/app/config_manager.py
import threading, json, shutil, logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger("mynas.config")
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"
BACKUP_DIR = CONFIG_DIR / "backups"

_lock = threading.Lock()

class ConfigManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.data = {}
        self.ensure_initialized()

    def ensure_initialized(self):
        if not CONFIG_FILE.exists():
            self.data = self._default_config()
            self._save_to_disk(self.data)
        else:
            self.reload()

    def reload(self) -> Dict[str, Any]:
        with _lock:
            try:
                self.data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("config read error: %s", e)
                self.data = self._default_config()
                self._save_to_disk(self.data)
            return self.data

    def save(self, data: Dict[str, Any]=None):
        with _lock:
            if data is not None:
                self.data = data
            self._create_backup()
            self._save_to_disk(self.data)

    def _save_to_disk(self, data):
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _create_backup(self):
        if CONFIG_FILE.exists():
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            bk = BACKUP_DIR / f"config_{ts}.json"
            shutil.copy(CONFIG_FILE, bk)
            # keep latest 10
            backups = sorted(BACKUP_DIR.glob("config_*.json"), reverse=True)
            for old in backups[10:]:
                try: old.unlink()
                except: pass

    # generic section helpers
    def get_section(self, section: str):
        return self.data.get(section, {})

    def set_section(self, section: str, value):
        self.data[section] = value
        self.save()

    # storage helpers
    def get_storage(self):
        return self.data.get("storage", {"pools": [], "datasets": []})

    def update_storage(self, storage_data):
        self.data["storage"] = storage_data
        self.save()

    # users / shares / acls
    def list_users(self):
        return self.data.get("users", [])

    def add_user(self, user_obj):
        users = self.data.setdefault("users", [])
        users.append(user_obj)
        self.save()

    def remove_user(self, username):
        users = [u for u in self.data.get("users", []) if u.get("username") != username]
        self.data["users"] = users
        self.save()

    def list_shares(self):
        return self.data.get("shares", [])

    def add_share(self, share_obj):
        shares = self.data.setdefault("shares", [])
        shares.append(share_obj)
        self.save()

    def remove_share(self, name):
        shares = [s for s in self.data.get("shares", []) if s.get("name") != name]
        self.data["shares"] = shares
        self.save()

    def list_acls(self):
        return self.data.get("acl", [])

    def add_acl(self, acl_entry):
        acls = self.data.setdefault("acl", [])
        acls.append(acl_entry)
        self.save()

    def remove_acl(self, path, username):
        acls = [a for a in self.data.get("acl", []) if not (a["path"]==path and a["user"]==username)]
        self.data["acl"] = acls
        self.save()

    # system section
    def get_network(self):
        return self.data.get("network", {})

    def update_network(self, new):
        self.data["network"] = new
        self.save()

    def _default_config(self):
        return {
            "system": {
                "hostname": "mynas",
                "storage_backend": "json",  # json | sqlite | mysql
                "version": "1.0.0",
            },
            "users": [{"username":"admin","role":"admin","password":"admin"}],
            "storage": {"pools": [], "datasets": []},
            "shares": [],
            "acl": [],
            "network": {},
            "disks": []
        }

# global instance
_cfg = ConfigManager()
def get_config(): return _cfg.reload()
def save_config(data): _cfg.save(data)
def ensure_config_ready(): _cfg.ensure_initialized()
cfg = _cfg
