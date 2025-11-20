# backend/app/task_queue.py
import threading
import queue
import time
import json
import uuid
from typing import Dict, Any, Optional, List
from backend.realtime.websocket_server import WSManagerProxy
from backend.drivers.driver_loader import get_driver
import sqlite3, os
import pymysql

# Persistence uses same DB as drivers or a local sqlite fallback
DB_SQLITE = os.environ.get("MYNAS_TASK_DB", "/var/lib/mynas/tasks.db")
USE_MYSQL = os.environ.get("MYNAS_TASK_DB_TYPE", "").lower() == "mysql"

# Task shape
# {
#   "id": "uuid",
#   "status": "pending|running|success|failed",
#   "type": "create_pool",
#   "payload": {...},
#   "progress": 0,
#   "result": {...}
# }

_task_queue = queue.Queue()
_worker_thread = None
_stop_event = threading.Event()

def _init_sqlite():
    os.makedirs(os.path.dirname(DB_SQLITE), exist_ok=True)
    conn = sqlite3.connect(DB_SQLITE, check_same_thread=False)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        type TEXT,
        payload TEXT,
        status TEXT,
        progress INTEGER,
        result TEXT,
        created_ts REAL,
        updated_ts REAL
    )
    """)
    conn.commit()
    return conn

def _init_mysql():
    # use env vars - assume migration already created tasks table in MySQL
    import pymysql
    conn = pymysql.connect(
        host=os.environ.get("MYNAS_MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYNAS_MYSQL_PORT", "3306")),
        user=os.environ.get("MYNAS_MYSQL_USER", "mynas"),
        password=os.environ.get("MYNAS_MYSQL_PASS", "mynas"),
        database=os.environ.get("MYNAS_MYSQL_DB", "mynas"),
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(64) PRIMARY KEY,
            type VARCHAR(128),
            payload JSON,
            status VARCHAR(32),
            progress INT,
            result JSON,
            created_ts DOUBLE,
            updated_ts DOUBLE
        )
        """)
    return conn

# choose persistence
if USE_MYSQL:
    _pconn = _init_mysql()
    _use_sqlite = False
else:
    _pconn = _init_sqlite()
    _use_sqlite = True

def _persist_task(task: Dict[str, Any]):
    now = time.time()
    if _use_sqlite:
        cur = _pconn.cursor()
        cur.execute("INSERT OR REPLACE INTO tasks (id,type,payload,status,progress,result,created_ts,updated_ts) VALUES (?,?,?,?,?,?,?,?)",
                    (task["id"], task["type"], json.dumps(task["payload"]), task["status"], int(task.get("progress",0)), json.dumps(task.get("result",{})), task.get("created_ts", now), now))
        _pconn.commit()
    else:
        with _pconn.cursor() as cur:
            cur.execute("REPLACE INTO tasks (id,type,payload,status,progress,result,created_ts,updated_ts) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (task["id"], task["type"], json.dumps(task["payload"]), task["status"], int(task.get("progress",0)), json.dumps(task.get("result",{})), task.get("created_ts", now), now))

def _update_task_status(task_id: str, status: str, progress: Optional[int]=None, result: Optional[Dict]=None):
    now = time.time()
    if _use_sqlite:
        cur = _pconn.cursor()
        if progress is None and result is None:
            cur.execute("UPDATE tasks SET status=?, updated_ts=? WHERE id=?", (status, now, task_id))
        else:
            cur.execute("UPDATE tasks SET status=?, progress=?, result=?, updated_ts=? WHERE id=?",
                        (status, int(progress or 0), json.dumps(result or {}), now, task_id))
        _pconn.commit()
    else:
        with _pconn.cursor() as cur:
            cur.execute("UPDATE tasks SET status=%s, progress=%s, result=%s, updated_ts=%s WHERE id=%s",
                        (status, int(progress or 0), json.dumps(result or {}), now, task_id))

    # broadcast via websocket
    WSManagerProxy.broadcast({"module": "tasks", "task_id": task_id, "status": status, "progress": progress or 0, "result": result})

def enqueue_task(task_type: str, payload: Dict[str, Any]) -> str:
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "type": task_type,
        "payload": payload,
        "status": "pending",
        "progress": 0,
        "result": {},
        "created_ts": time.time(),
    }
    _persist_task(task)
    _task_queue.put(task)
    # broadcast pending
    WSManagerProxy.broadcast({"module": "tasks", "task_id": task_id, "status": "pending", "progress": 0})
    return task_id

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    if _use_sqlite:
        cur = _pconn.cursor()
        cur.execute("SELECT id,type,payload,status,progress,result,created_ts,updated_ts FROM tasks WHERE id=?", (task_id,))
        r = cur.fetchone()
        if not r: return None
        return {"id": r[0], "type": r[1], "payload": json.loads(r[2]), "status": r[3], "progress": r[4], "result": json.loads(r[5] or "{}"), "created_ts": r[6], "updated_ts": r[7]}
    else:
        with _pconn.cursor() as cur:
            cur.execute("SELECT id,type,payload,status,progress,result,created_ts,updated_ts FROM tasks WHERE id=%s", (task_id,))
            r = cur.fetchone()
            if not r: return None
            return {"id": r["id"], "type": r["type"], "payload": json.loads(r["payload"]), "status": r["status"], "progress": r["progress"], "result": r["result"] or {}, "created_ts": r["created_ts"], "updated_ts": r["updated_ts"]}

def list_all_tasks(limit: int=50) -> List[Dict[str, Any]]:
    if _use_sqlite:
        cur = _pconn.cursor()
        cur.execute("SELECT id,type,payload,status,progress,result,created_ts,updated_ts FROM tasks ORDER BY created_ts DESC LIMIT ?", (limit,))
        rows = []
        for r in cur.fetchall():
            rows.append({"id": r[0], "type": r[1], "payload": json.loads(r[2]), "status": r[3], "progress": r[4], "result": json.loads(r[5] or "{}")})
        return rows
    else:
        with _pconn.cursor() as cur:
            cur.execute("SELECT id,type,payload,status,progress,result,created_ts,updated_ts FROM tasks ORDER BY created_ts DESC LIMIT %s", (limit,))
            rows = []
            for r in cur.fetchall():
                rows.append({"id": r["id"], "type": r["type"], "payload": json.loads(r["payload"]), "status": r["status"], "progress": r["progress"], "result": r["result"] or {}})
            return rows

# Worker task implementation: supports create_pool currently
def _worker_loop():
    driver = get_driver()
    while not _stop_event.is_set():
        try:
            task = _task_queue.get(timeout=1)
        except queue.Empty:
            continue
        task_id = task["id"]
        ttype = task["type"]
        _update_task_status(task_id, "running", 1, {})
        try:
            if ttype == "create_pool":
                payload = task["payload"]
                name = payload.get("name")
                layout = payload.get("layout", {})
                # progress update: 10% reserved for validation
                _update_task_status(task_id, "running", 5, {"step":"validate"})
                # run driver create_pool (blocking)
                res = driver.create_pool(name, layout, dry_run=False)
                if res.get("created"):
                    _update_task_status(task_id, "success", 100, {"pool": name})
                else:
                    _update_task_status(task_id, "failed", 0, {"error": res.get("error")})
            else:
                # unknown task type
                _update_task_status(task_id, "failed", 0, {"error": "unknown task type"})
        except Exception as e:
            _update_task_status(task_id, "failed", 0, {"error": str(e)})
        finally:
            _task_queue.task_done()

def start_background_worker():
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return
    _stop_event.clear()
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
    _worker_thread.start()

def stop_background_worker():
    _stop_event.set()
    if _worker_thread:
        _worker_thread.join(timeout=2)
