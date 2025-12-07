# backend/app/db_config_manager.py
"""
DB-backed ConfigManager replacement.
Provides key/value store plus helper accessors for lists previously stored in config.json.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from backend.drivers.db import run_query

logger = logging.getLogger("mynas.dbconfig")


async def set_setting(key: str, value: Any):
    txt = json.dumps(value) if not isinstance(value, str) else value
    q = """
    INSERT INTO system_settings (key_name, value_text)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE value_text = VALUES(value_text)
    """
    await run_query(q, (key, txt), fetch="none")
    return True


async def get_setting(key: str, default: Any = None):
    q = "SELECT value_text FROM system_settings WHERE key_name=%s LIMIT 1"
    r = await run_query(q, (key,), fetch="one")
    if not r:
        return default
    v = r.get("value_text")
    try:
        return json.loads(v)
    except Exception:
        return v


# helpers for lists previously in config.json
async def list_acls() -> List[Dict[str, Any]]:
    rows = await run_query("SELECT path, subject_type, subject, permissions FROM acl ORDER BY id DESC", (), fetch="all")
    return [{"path": r["path"], "type": r["subject_type"], "subject": r["subject"], "permissions": r["permissions"]} for r in rows]

async def add_acl_entry(path: str, subject: str, permissions: str, subject_type: str = "user"):
    q = "INSERT INTO acl (path, subject_type, subject, permissions) VALUES (%s,%s,%s,%s)"
    await run_query(q, (path, subject_type, subject, permissions), fetch="none")
    return True

async def remove_acl_entry(path: str, subject: str):
    q = "DELETE FROM acl WHERE path=%s AND subject=%s"
    await run_query(q, (path, subject), fetch="none")
    return True
