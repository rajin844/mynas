# backend/app/db.py
"""
Async MySQL helper using aiomysql.

Provides:
 - init_pool(dsn_or_kwargs)
 - close_pool()
 - run_query(sql, params) -> rows (list of dict)
 - run_statement(sql, params) -> affected / lastrowid
Supports named params like :name and converts to %s for aiomysql.
"""

import re
import aiomysql
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("mynas.db")

_pool: Optional[aiomysql.Pool] = None

_param_re = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")

def _convert_sql_and_params(sql: str, params: Optional[Dict[str, Any]]) -> Tuple[str, List[Any]]:
    """
    Convert SQL with :name placeholders to %s placeholders and return param values list in the order found.
    Example:
      "SELECT * FROM t WHERE name=:name AND id=:id"
      params={"name":"x","id":10}
    -> ("SELECT * FROM t WHERE name=%s AND id=%s", ["x", 10])
    """
    if not params:
        # replace named placeholders with %s but no params
        sql2 = _param_re.sub("%s", sql)
        return sql2, []
    keys: List[str] = []
    def _sub(m):
        keys.append(m.group(1))
        return "%s"
    sql2 = _param_re.sub(_sub, sql)
    values = [params.get(k) for k in keys]
    return sql2, values

async def init_pool(host: str = "127.0.0.1", port: int = 3306,
                    user: str = "mynas", password: str = "Admin@1234", db: str = "mynas",
                    minsize: int = 1, maxsize: int = 10, loop: Optional[asyncio.AbstractEventLoop] = None):
    global _pool
    if _pool is not None:
        return _pool
    if loop is None:
        loop = asyncio.get_event_loop()
    _pool = await aiomysql.create_pool(host=host, port=port, user=user, password=password,
                                      db=db, minsize=minsize, maxsize=maxsize, autocommit=True, loop=loop)
    logger.info("MySQL pool initialized (%s@%s:%s/%s)", user, host, port, db)
    return _pool

async def close_pool():
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        logger.info("MySQL pool closed")

async def run_query(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute SELECT-style query and return rows as list of dict.
    """
    global _pool
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call init_pool(...) first.")
    sql2, vals = _convert_sql_and_params(sql, params)
    async with _pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql2, vals)
            rows = await cur.fetchall()
            return [dict(r) for r in rows] if rows else []

async def fetch_one(sql: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """
    Execute a SELECT … LIMIT 1 query and return exactly one row.
    Named params (:name) are converted to %s placeholders automatically.

    Returns:
        dict(row)   → if found
        None        → if nothing returned
    """
    global _pool
    if _pool is None:
        raise RuntimeError("MySQL pool not initialized")

    params = params or {}

    # Convert :param → %s
    sql2, vals = _convert_sql_and_params(sql, params)

    async with _pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            try:
                await cur.execute(sql2, vals)
                row = await cur.fetchone()
                return row if row else None
            except Exception as e:
                logger.error(f"fetch_one() SQL error: {e} | SQL={sql2}, vals={vals}")
                return None           

async def run_statement(sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute INSERT/UPDATE/DELETE. Returns dict: {"rowcount": int, "lastrowid": int}.
    """
    global _pool
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call init_pool(...) first.")
    sql2, vals = _convert_sql_and_params(sql, params)
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql2, vals)
            lastid = cur.lastrowid
            rowcount = cur.rowcount
            return {"rowcount": rowcount, "lastrowid": lastid}

async def run_execute(sql: str, params: Optional[Dict[str, Any]] = None) -> int:
    """
    Execute UPDATE / DELETE or any statement that does not return rows.
    Returns:
      rowcount (int)
    """
    global _pool
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call init_pool(...) first.")
    sql2, vals = _convert_sql_and_params(sql, params)

    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql2, vals)
            return cur.rowcount

async def run_insert(sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute an INSERT query.
    Returns:
      {"lastrowid": int, "rowcount": int}
    """
    global _pool
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call init_pool(...) first.")
    sql2, vals = _convert_sql_and_params(sql, params)

    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql2, vals)
            return {
                "lastrowid": cur.lastrowid,
                "rowcount": cur.rowcount
            }      

def safe_exec_sync(cmd: List[str], timeout: int = 15):
    """
    Sync safe-exec for migrations/boot.
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            text=True,
        )
        return {
            "ok": result.returncode == 0,
            "code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except Exception as e:
        logger.error("safe_exec_sync error: %s", e)
        raise      
    
                
