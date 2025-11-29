"""
MyNAS Async MySQL Database Layer (FINAL + FIXED)
-----------------------------------------------
✓ Async SQLAlchemy 2.0 Engine (aiomysql)
✓ High-performance pool
✓ Safe transaction wrapper
✓ run_query() fully working
✓ fetch_one() fully working
✓ raw() helper
✓ db_ping() & init_db()
"""

import os
import logging
import urllib.parse
import subprocess
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text
from contextlib import asynccontextmanager

logger = logging.getLogger("mynas.db")

# ========================================================================
# MYSQL CONFIG
# ========================================================================

DB_USER = os.getenv("MYSQL_USER", "mynas")
DB_PASS_RAW = os.getenv("MYSQL_PASSWORD", "Admin@1234")
DB_PASS = urllib.parse.quote_plus(DB_PASS_RAW)
DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "mynas")

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ========================================================================
# ASYNC ENGINE + SESSIONMAKER
# ========================================================================

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_recycle=1800,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()

# ========================================================================
# SAFE SESSION WRAPPER
# ========================================================================

@asynccontextmanager
async def async_session() -> AsyncSession:
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("DB session failed: %s", e)
        raise
    finally:
        await session.close()

# ========================================================================
# HEALTH CHECK
# ========================================================================

async def db_ping() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("DB ping failed: %s", e)
        return False

# ========================================================================
# init_db() — called on backend startup
# ========================================================================

async def init_db():
    logger.info("🔌 Testing MySQL connection...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ MySQL connection OK")
    except Exception as e:
        logger.error("❌ MySQL connection FAILED: %s", e)
        raise RuntimeError("Could not connect to MySQL") from e

# ========================================================================
# RAW SQL HELPER
# ========================================================================

async def raw(sql: str, params: Optional[dict] = None):
    async with engine.begin() as conn:
        res = await conn.execute(text(sql), params or {})
        try:
            rows = res.mappings().all()
            return [dict(r) for r in rows]
        except Exception:
            return None

# ========================================================================
# run_query() — main SQL helper (FULL FIX)
# ========================================================================

async def run_query(sql: str, params: Optional[Dict[str, Any]] = None, fetch: bool = True) -> Any:
    """
    Execute SQL text with named params. If fetch True, returns list of rows as dicts.
    Minimal helper used by migration and simple managers.
    """
    async with async_session() as session:
        try:
            result = await session.execute(text(sql), params or {})
            if fetch:
                rows = result.mappings().all()
               
                return [dict(r) for r in rows]
            else:

                return {"rows_affected": result.rowcount}
        except Exception as e:
            logger.exception("DB query failed: %s | params=%s", e, params)
            await session.rollback()
            raise

# Convenience single-row fetch
async def fetch_one(sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    rows = await run_query(sql, params=params, fetch=True)
    return rows[0] if rows else None

def safe_exec_sync(cmd: list[str], sudo: bool = False, timeout: int = 15):
    full_cmd = ["sudo"] + cmd if sudo else cmd
    try:
        result = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            text=True
        )
        return {
            "ok": result.returncode == 0,
            "code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except Exception as e:
        raise ExecError(f"safe_exec_sync error: {e}")
