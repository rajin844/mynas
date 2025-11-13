# backend/app/utils/json_db.py
import json
import threading
from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"
BACKUP_DIR = CONFIG_DIR / "backups"
LOCK = threading.Lock()
MAX_BACKUPS = 20

def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def read_config():
    ensure_dirs()
    with LOCK:
        if not CONFIG_FILE.exists():
            # return default skeleton
            default = {
                "system": {"hostname": "mynas"},
                "users": [],
                "storage": {"pools": [], "datasets": []},
                "shares": [],
                "acl": [],
                "backups": []
            }
            CONFIG_FILE.write_text(json.dumps(default, indent=2))
            return default
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

def write_config(obj):
    ensure_dirs()
    with LOCK:
        # create a timestamped backup of current file if exists
        if CONFIG_FILE.exists():
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            backup = BACKUP_DIR / f"config_{ts}.json"
            shutil.copy(CONFIG_FILE, backup)
            _cleanup_old_backups()
        CONFIG_FILE.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        return True

def load_config(obj):
    ensure_dirs()
    with LOCK:
        # create a timestamped backup of current file if exists
        if CONFIG_FILE.exists():
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            backup = BACKUP_DIR / f"config_{ts}.json"
            shutil.copy(CONFIG_FILE, backup)
            _cleanup_old_backups()
        CONFIG_FILE.loads (json.dumps(obj, indent=2), encoding="utf-8")
        return True        

def _cleanup_old_backups():
    files = sorted(BACKUP_DIR.glob("config_*.json"), reverse=True)
    for f in files[MAX_BACKUPS:]:
        try:
            f.unlink()
        except Exception:
            pass

def list_backups():
    ensure_dirs()
    files = sorted(BACKUP_DIR.glob("config_*.json"), reverse=True)
    return [f.name for f in files]

def restore_backup(filename):
    ensure_dirs()
    src = BACKUP_DIR / filename
    if not src.exists():
        return False
    shutil.copy(src, CONFIG_FILE)
    return True
