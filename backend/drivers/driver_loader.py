# backend/drivers/driver_loader.py
from backend.app.config_manager import cfg
import importlib
from typing import Any

def get_backend_mode():
    # config "system": {"storage_backend": "json"|"sqlite"|"mysql"}
    sys_conf = cfg.get_section("system") or {}
    return sys_conf.get("storage_backend", "json").lower()

_driver_instance = None

def load_driver():
    global _driver_instance
    mode = get_backend_mode()
    if _driver_instance is not None:
        return _driver_instance

    if mode == "sqlite":
        mod = importlib.import_module("backend.drivers.sqlite_driver")
        _driver_instance = mod.SQLiteDriver(cfg)
    elif mode == "mysql":
        mod = importlib.import_module("backend.drivers.mysql_driver")
        _driver_instance = mod.MySQLDriver(cfg)
    else:
        # default JSON driver (uses config_manager)
        mod = importlib.import_module("backend.drivers.json_driver")
        _driver_instance = mod.JSONDriver(cfg)
    return _driver_instance

def get_driver():
    return load_driver()
