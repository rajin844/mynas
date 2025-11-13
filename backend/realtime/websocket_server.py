# backend/app/ws_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json
import random
from typing import List, Dict, Any

# --- WebSocket Manager Classes ---

class WSManager:
    """Handles all active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
        print(f"✅ Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            print(f"❌ Client disconnected. Remaining: {len(self.active_connections)}")
        except ValueError:
            pass

    def client_count(self) -> int:
        """Return number of connected WebSocket clients."""
        return len(self.active_connections)

    async def broadcast(self, message: Dict[str, Any]):
        """Send JSON to all connected clients."""
        remove_list = []
        for ws in list(self.active_connections):
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"⚠️ Error sending to client: {e}")
                remove_list.append(ws)
        for ws in remove_list:
            self.disconnect(ws)


class WSManagerProxy:
    """Allows other modules to broadcast without holding the WSManager reference."""
    _ws_manager: WSManager = None

    @classmethod
    def register(cls, ws_manager: WSManager):
        cls._ws_manager = ws_manager

    @classmethod
    def broadcast(cls, msg: Dict[str, Any]):
        if cls._ws_manager:
            asyncio.create_task(cls._ws_manager.broadcast(msg))


# --- FastAPI app setup ---

app = FastAPI(title="NAS Manager WebSocket Server")

ws_manager = WSManager()
WSManagerProxy.register(ws_manager)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle client WebSocket connection."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"raw": data}

            print(f"📩 Received from client: {payload}")

            # Echo message back to client
            await websocket.send_json({"event": "echo", "data": payload})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# --- Background broadcast task ---
async def broadcast_task():
    """Send updates periodically to all connected clients."""
    while True:
        if ws_manager.client_count() > 0:
            msg = {
                "event": "update_status",
                "value": random.choice(["pool_ok", "dataset_modified", "share_updated"]),
            }
            await ws_manager.broadcast(msg)
        await asyncio.sleep(5)


# --- Run background task on startup ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_task())
    print("✅ WebSocket broadcast task started.")


# --- Optional test homepage ---
@app.get("/")
async def home():
    return HTMLResponse("""
    <html>
    <body>
        <h2>NAS Manager WebSocket Server</h2>
        <p>Connect via ws://localhost:6789/ws</p>
    </body>
    </html>
    """)

# --- Run with: uvicorn ws_server:app --host 0.0.0.0 --port 6789 ---
