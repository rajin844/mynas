# backend/drivers/driver_loader.py
import importlib
from backend.app.config_manager import cfg
from typing import Optional

_driver = None

def get_backend_mode() -> str:
    # system.storage_backend can be: json, sqlite, mysql, zfs, ext4, btrfs, cloud (prefer db-backed)
    sysconf = cfg.get_section("system") or {}
    return sysconf.get("storage_backend", "json").lower()

def auto_detect_backend() -> str:
    """
    Basic heuristics:
      - if zpool present and zfs utilities present => zfs
      - else if /etc/fstab has ext4 mounts => ext4
      - else fallback to sqlite or json based on config
    """
    import shutil, subprocess
    if shutil.which("zpool") and shutil.which("zfs"):
        return "zfs"
    if shutil.which("mkfs.ext4"):
        return "ext4"
    if shutil.which("mkfs.btrfs"):
        return "btrfs"
    # fallback
    return get_backend_mode()

def load_driver() -> object:
    global _driver
    if _driver:
        return _driver
    mode = get_backend_mode()
    if mode == "auto":
        mode = auto_detect_backend()

    # map mode to driver module/class
    mapping = {
        "json": ("backend.drivers.json_driver", "JSONDriver"),
        "zfs": ("backend.drivers.zfs_driver", "ZfsDriver"),
        "ext4": ("backend.drivers.ext4_driver", "Ext4Driver"),
        "btrfs": ("backend.drivers.btrfs_driver", "BtrfsDriver"),
        "cloud": ("backend.drivers.cloud_driver", "CloudDriver"),
        "sqlite": ("backend.drivers.sqlite_driver", "SQLiteDriver"),
        "mysql": ("backend.drivers.mysql_driver", "MySQLDriver"),
    }
    if mode not in mapping:
        mode = "json"
    modname, clsname = mapping[mode]
    mod = importlib.import_module(modname)
    cls = getattr(mod, clsname)
    # SQLite/MySQL drivers expect cfg; json/zfs/ext4 drivers use no args or cfg
    try:
        _driver = cls(cfg)
    except TypeError:
        _driver = cls()
    return _driver

def get_driver():
    return load_driver()
