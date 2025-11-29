# backend/app/migrate.py
import os
import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from backend.drivers.db import DATABASE_URL, engine, safe_exec_sync 

MIGRATIONS_DIR = Path(__file__).parent 
SCHEMA_TABLE = "schema_migrations"

async def ensure_migrations_table():
    async with engine.begin() as conn:
        await conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_TABLE} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """))

async def applied_migrations():
    async with engine.begin() as conn:
        res = await conn.execute(text(f"SELECT name FROM {SCHEMA_TABLE} ORDER BY id"))
        rows =  res.fetchall()
        return {r[0] for r in rows}

async def apply_migration_file(path: Path):
    sql = path.read_text(encoding="utf-8")
    async with engine.begin() as conn:
        await conn.execute(text(sql))
        await conn.execute(text(f"INSERT INTO {SCHEMA_TABLE} (name) VALUES (:name)"), {"name": path.name})
        print(f"Applied {path.name}")

async def run_migrations():
    await ensure_migrations_table()
    applied = await applied_migrations()
    files = sorted([p for p in MIGRATIONS_DIR.glob("*.sql")])
    for f in files:
        if f.name in applied:
            continue
        print("Applying:", f.name)
        await apply_migration_file(f)

if __name__ == "__main__":
    asyncio.run(run_migrations())
