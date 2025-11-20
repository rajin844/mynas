"""
backend/app/user_manager.py
---------------------------
Handles user management and persistence in config.json.
"""

from typing import List, Dict, Any
from backend.app.config_manager import cfg
from backend.realtime.websocket_server import WSManagerProxy

def _try_broadcast(message: dict):
    try:
        from realtime.websocket_server import WSManagerProxy
        WSManagerProxy.broadcast(message)
    except Exception:
        pass


def list_users() -> List[Dict[str, Any]]:
    return cfg.list_users()

def get_user(username: str) -> Dict[str, Any]:
    for u in cfg.list_users():
        if u["username"] == username:
            return u
    return {}

def create_user(username: str, password: str, role: str = "user") -> bool:
    users = cfg.list_users()
    if any(u["username"] == username for u in users):
        return False
    users.append({"username": username, "password": password, "role": role})
    cfg.set_section("users", users)
    WSManagerProxy.broadcast({"event": "user_created", "user": username})
    return True

def update_user(username: str, data: Dict[str, Any]) -> bool:
    users = cfg.list_users()
    for u in users:
        if u["username"] == username:
            u.update(data)
            cfg.set_section("users", users)
            WSManagerProxy.broadcast({"event": "user_updated", "user": username})
            return True
    return False

def delete_user(username: str) -> bool:
    users = cfg.list_users()
    if not any(u["username"] == username for u in users):
        return False
    users = [u for u in users if u["username"] != username]
    cfg.set_section("users", users)
    WSManagerProxy.broadcast({"event": "user_deleted", "user": username})
    return True

