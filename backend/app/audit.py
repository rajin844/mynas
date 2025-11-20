"""
Simple audit logger for MyNAS.
Writes JSON-lines to a file (append-only).
"""

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("mynas.audit")
AUDIT_LOG_PATH = Path("/var/log/mynas_audit.log")  # change to config-managed path

def _ensure_path():
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

def log_event(event: str, actor: str = "system", path: str = "", details: dict = None):
    _ensure_path()
    entry = {
        "ts": int(time.time()),
        "event": event,
        "actor": actor,
        "path": path,
        "details": details or {}
    }
    try:
        with open(AUDIT_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.exception("Failed to write audit log: %s", e)
    logger.debug("Audit: %s %s", event, actor)
