# Small helper to emit events via global ws manager
# mynas/backend/app/realtime/events.py
from typing import Dict, Any
import logging
from backend.realtime.websocket_server import WSManager
_global_ws = None

logger = logging.getLogger("mynas.realtime.events")

def register_ws(ws: WSManager):
    global _global_ws
    _global_ws = ws

# We import lazily to avoid circular imports at module import time
def broadcast_event(message: Dict[str, Any]):
    """
    Broadcasts a message using ws_manager if available.
    Message should be JSON-serializable (dict).
    """
    try:
        # import on call so that the runtime has initialized ws_manager
        ws.broadcast(message)
        logger.debug("Broadcast event: %s", message)
    except Exception as e:
        logger.exception("Failed to broadcast event: %s", e)

emit_event = broadcast_event        




