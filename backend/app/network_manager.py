# backend/network/network_manager.py
import subprocess
from typing import Dict

def get_network_interfaces():
    try:
        out = subprocess.check_output(["ip","-j","a"]).decode()
        import json
        return json.loads(out)
    except:
        return []

def apply_network_settings(meta: Dict):
    # Save to config.json
    from backend.app.config_manager import cfg
    cfg.set_section("network", meta)
    return {"updated": True}
