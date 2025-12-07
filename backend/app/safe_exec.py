# backend/app/safe_exec.py
"""
High-performance secure subprocess wrapper for MyNAS
----------------------------------------------------
Features:
 - Non-blocking async exec
 - Timeout protection
 - Sanitized args (no shell injection)
 - Captures stdout/stderr safely
 - Structured JSON-friendly response
 - Optional sudo passthrough
"""

import asyncio
import shlex
import logging

logger = logging.getLogger("mynas.safe_exec")


class ExecError(Exception):
    pass


async def safe_exec(cmd: list[str], timeout: int = 20, sudo: bool = False):
    """
    Run command safely:
    - cmd: ["zfs", "list", "-H"]
    - no shell=True (prevents injection)
    - async + timeout
    """
    if not isinstance(cmd, list):
        raise ValueError("safe_exec: cmd must be a list")

    full_cmd = ["sudo"] + cmd if sudo else cmd

    logger.debug(f"[exec] Running command: {full_cmd}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise ExecError(f"Command timed out: {full_cmd}")

        stdout = stdout.decode().strip()
        stderr = stderr.decode().strip()

        logger.debug(f"[exec] exit={proc.returncode}, out={stdout}, err={stderr}")

        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr
        }

    except FileNotFoundError:
        raise ExecError(f"Command not found: {cmd[0]}")
    except Exception as e:
        raise ExecError(f"safe_exec failed: {e}")
