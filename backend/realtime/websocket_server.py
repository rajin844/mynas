# backend/app/ws_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json
import random
import logging
from typing import Set, Callable, Any, Optional
from typing import List, Dict, Any

import websockets
from websockets.server import WebSocketServerProtocol


logger = logging.getLogger("mynas.ws")

# ---------------------------------------------------------------------------
# WS Manager - keeps connection set and provides broadcast helper
# ---------------------------------------------------------------------------
class WSManager:
    def __init__(self):
        self._clients: Set[WebSocketServerProtocol] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: WebSocketServerProtocol):
        async with self._lock:
            self._clients.add(ws)
        logger.info("WS client connected: %s", ws.remote_address)

    async def unregister(self, ws: WebSocketServerProtocol):
        async with self._lock:
            self._clients.discard(ws)
        logger.info("WS client disconnected: %s", ws.remote_address)

    async def send(self, ws: WebSocketServerProtocol, obj: Any):
        try:
            await ws.send(json.dumps(obj))
        except Exception as e:
            logger.debug("Send failed %s: %s", ws.remote_address, e)

    async def broadcast(self, obj: Any):
        """Send obj to all connected clients (JSON)"""
        data = json.dumps(obj)
        to_remove = []
        async with self._lock:
            clients = list(self._clients)
        for ws in clients:
            try:
                await ws.send(data)
            except Exception:
                logger.debug("Broadcast failed for %s", ws.remote_address)
                to_remove.append(ws)
        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self._clients.discard(ws)

    def client_count(self) -> int:
        return len(self._clients)

# proxy/global holder so other modules can call WSManagerProxy.broadcast(...)
class WSManagerProxy:
    _manager: Optional[WSManager] = None

    @classmethod
    def register(cls, manager: WSManager) -> None:
        cls._manager = manager

    @classmethod
    async def broadcast(cls, obj: Any) -> None:
        if cls._manager:
            await cls._manager.broadcast(obj)

    @classmethod
    def broadcast_sync(cls, obj: Any) -> None:
        """
        Convenience synchronous wrapper (fire-and-forget).
        Use when calling from non-async code. It schedules the broadcast on the running loop.
        """
        mgr = cls._manager
        if not mgr:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(mgr.broadcast(obj))
        except RuntimeError:
            # no running loop; best-effort: spawn a new loop in a thread (rare)
            asyncio.run(mgr.broadcast(obj))


# ---------------------------------------------------------------------------
# WebSocket handler
# ---------------------------------------------------------------------------
async def _ws_handler(ws: WebSocketServerProtocol, path: str):
    """
    Protocol:
      - client may send JSON messages (we simply echo back or handle 'ping')
      - server can broadcast via WSManagerProxy.broadcast(...)
    """
    manager = WSManagerProxy._manager
    if manager is None:
        manager = WSManager()
        WSManagerProxy.register(manager)

    await manager.register(ws)
    try:
        # accept loop: receive messages
        async for raw in ws:
            try:
                # allow string or JSON
                try:
                    payload = json.loads(raw)
                except Exception:
                    payload = raw

                # simple ping handler
                if isinstance(payload, str) and payload.lower() in ("ping", "hello"):
                    await manager.send(ws, {"type": "pong"})
                    continue

                # If user sends JSON with type "echo", we echo
                if isinstance(payload, dict) and payload.get("type") == "echo":
                    await manager.send(ws, {"type": "echo", "data": payload.get("data")})
                    continue

                # default: no-op (could route to RPC)
            except Exception as e:
                logger.exception("Error processing ws message: %s", e)

    except websockets.ConnectionClosed:
        pass
    except Exception as e:
        logger.exception("WS connection error: %s", e)
    finally:
        await manager.unregister(ws)


# ---------------------------------------------------------------------------
# Start server helper (call from main.py startup)
# ---------------------------------------------------------------------------
def start_ws_server(loop: asyncio.AbstractEventLoop,
                    host: str = "0.0.0.0",
                    port: int = 6789,
                    origins: Optional[Set[str]] = None) -> websockets.server.serve:
    """
    Start the websockets server on provided loop.
    - origins: set of allowed origin strings (None to allow all)
    Returns the Serve object (awaitable) — but we schedule create_task() here.
    """
    # websockets.serve accepts origins param (list or None)
    logger.info("Starting WS server on %s:%d (origins=%s)", host, port, origins)
    coro = websockets.serve(_ws_handler, host, port, origins=origins, ping_interval=20, ping_timeout=20, max_size=2**20)
    # schedule the server onto the loop
    server = loop.run_until_complete(coro) if not loop.is_running() else loop.create_task(coro)
    return server
