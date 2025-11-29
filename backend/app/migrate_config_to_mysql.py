#!/usr/bin/env python3
"""
One-time migration tool:
Migrate old config.json → MySQL tables
"""

import json
import asyncio
from pathlib import Path

from backend.drivers.db import run_query  # async DB helper

CONFIG_PATH = Path("backend/config/config.json")


async def migrate():
    if not CONFIG_PATH.exists():
        print("❌ config.json not found.")
        return

    print("📥 Loading config.json...")
    data = json.loads(CONFIG_PATH.read_text())

    # ----------------------------
    # USERS
    # ----------------------------
    for u in data.get("users", []):
        await run_query(
            """
            INSERT INTO users (username, role, password)
            VALUES (:username, :role, :password)
            """,
            u,
            fetch=False,
        )
    print("✔ Users migrated")

    # ----------------------------
    # SHARES
    # ----------------------------
   # for s in data.get("shares", []):
    #    await run_query(
     #       """
      #      INSERT INTO shares (name, path)
       #     VALUES (:name, :path)
        #    """,
         #   s,
          #  fetch=False,
        #)
   # print("✔ Shares migrated")

    # ----------------------------
    # ACL
    # ----------------------------
    for a in data.get("acl", []):
        await run_query(
            """
            INSERT INTO acl (path, username, permissions)
            VALUES (:path, :user, :permissions)
            """,
            a,
            fetch=False,
        )
    print("✔ ACL migrated")

    # ----------------------------
    # STORAGE
    # ----------------------------
    st = data.get("storage", {})

    for p in st.get("pools", []):
        await run_query(
            """
            INSERT INTO pools (name, type)
            VALUES (:name, :type)
            """,
            p,
            fetch=False,
        )

    for d in st.get("datasets", []):
        await run_query(
            """
            INSERT INTO datasets (pool, name, mountpoint)
            VALUES (:pool, :name, :mountpoint)
            """,
            d,
            fetch=False,
        )

    print("✔ Storage migrated")

    # ----------------------------
    # SYSTEM SETTINGS
    # ----------------------------
    system = data.get("system", {})
    for key, value in system.items():
        await run_query(
            """
            INSERT INTO system_settings (key_name, value_json)
            VALUES (:k, :v)
            """,
            {"k": key, "v": json.dumps(value)},
            fetch=False,
        )
    print("✔ System settings migrated")

    print("\n🎉 Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())
