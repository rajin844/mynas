# backend/realtime/websocket_server.py
import json
import logging
from typing import Dict, Any, List

from fastapi import WebSocket

logger = logging.getLogger("mynas.ws")

class WSManager:
    """
    Instance managing WebSocket connections.
    Each websocket may have a list of subscribed modules.
    """

    def __init__(self):
        self._clients: List[WebSocket] = []
        self._subscriptions = {}  # WebSocket -> List[str]

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)
        # default subscribe to all modules so clients don't miss anything
        self._subscriptions[ws] = ["monitor", "zfs", "storage", "shares"]
        logger.debug("WS connected, subscribers count=%d", len(self._clients))

    async def disconnect(self, ws: WebSocket):
        try:
            await ws.close()
        except Exception:
            pass
        if ws in self._clients:
            self._clients.remove(ws)
        self._subscriptions.pop(ws, None)
        logger.debug("WS disconnected, subscribers count=%d", len(self._clients))

    async def handle_message(self, ws: WebSocket, msg: Dict[str, Any]):
        """
        Handle incoming messages from a client.
        Expected commands: {"action":"subscribe","modules":["monitor","zfs"]}
        """
        try:
            action = msg.get("action")
            if action == "subscribe":
                modules = msg.get("modules", [])
                if isinstance(modules, list):
                    self._subscriptions[ws] = modules
                    logger.debug("WS subscription updated: %s", modules)
            # add other client commands here as needed
        except Exception as e:
            logger.exception("handle_message error: %s", e)

    async def broadcast(self, module: str, data: Dict[str, Any]):
        """
        Broadcast a message to all clients subscribed to `module`.
        The outgoing message will be JSON: {"module": module, **data}
        """
        if not isinstance(data, dict):
            # normalize
            data = {"data": data}

        payload = {"module": module}
        payload.update(data)

        text = json.dumps(payload)
        dead = []

        for ws in list(self._clients):
            try:
                subs = self._subscriptions.get(ws)
                # if the client has a subscription list, only send if subscribed
                if subs is None or module in subs or "*" in subs:
                    await ws.send_text(text)
            except Exception:
                dead.append(ws)

        for ws in dead:
            await self.disconnect(ws)


# Proxy to access global manager from other modules
class WSManagerProxy:
    _manager: WSManager | None = None

    @classmethod
    def register(cls, manager: WSManager):
        cls._manager = manager

    @classmethod
    async def broadcast(cls, *args, **kwargs):
        """
        Flexible broadcast wrapper.

        Accepts either:
          await WSManagerProxy.broadcast("monitor", {"cpu": 1.2})
        or:
          await WSManagerProxy.broadcast({"module": "monitor", "cpu": 1.2, ...})

        or:
          await WSManagerProxy.broadcast(module="monitor", data={"cpu":...})
        """
        if cls._manager is None:
            logger.warning("WSManagerProxy.broadcast called but no manager registered")
            return

        # Case: single positional dict
        if len(args) == 1 and isinstance(args[0], dict) and "module" in args[0]:
            payload = args[0]
            module = payload.pop("module")
            data = payload  # remaining keys
            await cls._manager.broadcast(module, data)
            return

        # Case: (module, data)
        if len(args) == 2:
            module = args[0]
            data = args[1]
            await cls._manager.broadcast(module, data)
            return

        # Case: keyword usage: module=..., data=...
        module = kwargs.get("module")
        data = kwargs.get("data")
        if module:
            await cls._manager.broadcast(module, data or {})
            return

        # Unknown call signature
        logger.error("WSManagerProxy.broadcast called with unsupported args: %r %r", args, kwargs)
