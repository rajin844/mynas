# backend/app/safe_exec.py
import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("mynas.safe_exec")

async def safe_exec(cmd: List[str], timeout: int = 30, sudo: bool = False) -> Dict[str, Any]:
    """
    Execute a system command asynchronously and return dict:
      {"ok": True, "stdout": "...", "stderr": ""}
    """
    if sudo and cmd and cmd[0] != "sudo":
        cmd = ["sudo"] + cmd

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return {"ok": False, "stderr": "timeout"}
        return {"ok": proc.returncode == 0, "stdout": stdout.decode("utf-8", errors="ignore"), "stderr": stderr.decode("utf-8", errors="ignore")}
    except Exception as e:
        logger.exception("safe_exec failed: %s", e)
        return {"ok": False, "stderr": str(e)}
