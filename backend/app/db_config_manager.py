# backend/app/db_config_manager.py
"""
DBConfigManager
---------------
MySQL-backed configuration storage replacing config.json.

Features:
 - Global system settings
 - Network settings
 - UI flags
 - Boot flags
 - Dirty-module tracking
 - Arbitrary config sections (key/value JSON)

SQL Structure (MySQL):
    table: system_config
    columns:
        id (PK)
        section VARCHAR(64)
        key_name VARCHAR(128)
        value_json TEXT
"""

import json
import logging
from typing import Any, Dict, Optional

from backend.drivers.db import db # your async MySQL pool wrapper

logger = logging.getLogger("mynas.dbconfig")


class DBConfigManager:
    """
    Store config into a MySQL table `system_config`.
    Supports simple get/set operations for sections and keys.
    """

    TABLE = "system_config"

    async def init_table(self):
        """Create table if missing."""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            section VARCHAR(64) NOT NULL,
            key_name VARCHAR(128) NOT NULL,
            value_json TEXT,
            UNIQUE(section, key_name)
        );
        """
        await db.exec(sql)

    # -----------------------------------------------------------
    # Basic get
    # -----------------------------------------------------------
    async def get(self, section: str, key: str, default=None):
        sql = f"SELECT value_json FROM {self.TABLE} WHERE section=%s AND key_name=%s"
        row = await db.fetchrow(sql, (section, key))
        if not row:
            return default
        try:
            return json.loads(row["value_json"])
        except Exception:
            return default

    # -----------------------------------------------------------
    # Basic set
    # -----------------------------------------------------------
    async def set(self, section: str, key: str, value: Any):
        sql = f"""
        INSERT INTO {self.TABLE} (section, key_name, value_json)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE value_json=VALUES(value_json)
        """
        await db.exec(sql, (section, key, json.dumps(value)))

    # -----------------------------------------------------------
    # Fetch entire section
    # -----------------------------------------------------------
    async def get_section(self, section: str) -> Dict[str, Any]:
        sql = f"SELECT key_name, value_json FROM {self.TABLE} WHERE section=%s"
        rows = await db.fetchall(sql, (section,))
        out = {}
        for r in rows:
            try:
                out[r["key_name"]] = json.loads(r["value_json"])
            except Exception:
                out[r["key_name"]] = r["value_json"]
        return out

    # -----------------------------------------------------------
    # Replace entire section (dangerous)
    # -----------------------------------------------------------
    async def set_section(self, section: str, data: Dict[str, Any]):
        await db.exec(f"DELETE FROM {self.TABLE} WHERE section=%s", (section,))
        for k, v in data.items():
            await self.set(section, k, v)

    # -----------------------------------------------------------
    # Dirty module tracking
    # -----------------------------------------------------------
    async def mark_dirty(self, module: str):
        dirty = await self.get("system", "dirty_modules", [])
        if module not in dirty:
            dirty.append(module)
            await self.set("system", "dirty_modules", dirty)

    async def get_dirty(self):
        return await self.get("system", "dirty_modules", [])

    async def clear_dirty(self):
        await self.set("system", "dirty_modules", [])


# Global instance
dbconfig = DBConfigManager()
