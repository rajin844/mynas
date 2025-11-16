# backend/app/network_manager.py
"""
Network manager: list interfaces, update network config (persist), restart network (best-effort)
"""
import shutil
import subprocess
import logging
from typing import Dict, Any

from backend.app.config_manager import cfg
try:
    from backend.realtime.websocket_server import WSManagerProxy
except Exception:
    WSManagerProxy = None

logger = logging.getLogger("mynas.network")

def _has_cmd(name: str) -> bool:
    return shutil.which(name) is not None

def get_interfaces() -> Dict[str, Any]:
    """Return interface list via 'ip -j addr' when available or stored config."""
    if _has_cmd("ip"):
        try:
            out = subprocess.check_output(["ip", "-j", "addr"], text=True, stderr=subprocess.STDOUT)
            return {"raw": out}
        except Exception as e:
            logger.debug("ip addr failed: %s", e)
    return cfg.get("network", {})

def update_network(new_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Persist network config; optionally call nmcli/ip commands if available."""
    try:
        cfg.update_network(new_cfg)
        if WSManagerProxy:
            try:
                WSManagerProxy.broadcast({"module": "network", "event": "updated"})
            except Exception:
                pass
        # optional: apply using nmcli if present (not auto-applied here)
        return {"updated": True}
    except Exception as e:
        logger.exception("update_network failed: %s", e)
        return {"updated": False, "error": str(e)}

def restart_network() -> Dict[str, Any]:
    """Restart network service if systemctl present."""
    if _has_cmd("systemctl"):
        try:
            out = subprocess.check_output(["systemctl", "restart", "NetworkManager"], text=True, stderr=subprocess.STDOUT)
            return {"restarted": True, "output": out}
        except Exception as e:
            logger.exception("restart_network failed: %s", e)
            return {"restarted": False, "error": str(e)}
    return {"restarted": False, "error": "systemctl not available"}
