"""
Main NAS backend runner (FastAPI + WebSocket + Monitoring).

Run:  python run_nas.py
"""

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Local imports
from backend import user_manager, permissions, backup_manager
from storage import storage_manager, zfs_manager
from backend.monitoring import periodic_broadcast
from realtime.websocket_server import WSManagerProxy

app = FastAPI(title="MyNAS API v5")

# ---- CORS (allow frontend or localhost) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- WebSocket Manager ----
class WSManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                pass


ws_manager = WSManager()
WSManagerProxy.register(ws_manager)  # Allow other modules to broadcast

# ---- WebSocket endpoint ----
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ---------------------------------------------------------------------
#                      USER ROUTES
# ---------------------------------------------------------------------
@app.get("/api/users")
def list_users():
    return user_manager.list_users()


@app.post("/api/users")
def create_user(data: dict):
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")
    return user_manager.add_user(username, password, role)


@app.delete("/api/users/{username}")
def delete_user(username: str):
    ok = user_manager.delete_user(username)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


@app.post("/api/users/verify")
def verify_user(data: dict):
    username = data.get("username")
    password = data.get("password")
    valid = user_manager.verify_password(username, password)
    return {"valid": valid}


# ---------------------------------------------------------------------
#                      ACL ROUTES
# ---------------------------------------------------------------------
@app.post("/api/acl/apply")
def apply_acl(data: dict):
    path = data.get("path")
    username = data.get("username")
    perms = data.get("permissions")
    if not all([path, username, perms]):
        raise HTTPException(status_code=400, detail="Missing parameters")
    ok = permissions.apply_posix_acl(path, username, perms)
    return {"success": ok}


@app.post("/api/acl/remove")
def remove_acl(data: dict):
    path = data.get("path")
    username = data.get("username")
    if not all([path, username]):
        raise HTTPException(status_code=400, detail="Missing parameters")
    ok = permissions.remove_posix_acl(path, username)
    return {"success": ok}


# ---------------------------------------------------------------------
#                      BACKUP ROUTES
# ---------------------------------------------------------------------
@app.get("/api/backups")
def list_backups():
    return backup_manager.list_backups()


@app.post("/api/backups/create")
def create_backup():
    name = backup_manager.create_config_backup()
    return {"backup": name}


@app.post("/api/backups/restore")
def restore_backup(data: dict):
    filename = data.get("filename")
    ok = backup_manager.restore_config_backup(filename)
    if not ok:
        raise HTTPException(status_code=404, detail="Backup not found")
    return {"restored": filename}


@app.post("/api/backups/rsync")
def run_rsync(data: dict):
    source = data.get("source")
    dest = data.get("destination")
    ok = backup_manager.run_rsync_backup(source, dest)
    return {"success": ok}


# ---------------------------------------------------------------------
#                      DEMO SEQUENCE
# ---------------------------------------------------------------------
async def demo_sequence():
    """
    Automatically runs once at startup:
    - create demo user
    - create test ZFS pool and dataset
    - broadcasts events (verifiable via WebSocket)
    """
    await asyncio.sleep(1.0)
    print("⚙️ Running demo startup sequence...")

    try:
        user_manager.add_user("demo", "demo123", role="admin")
        print("✅ Demo user created")

        zfs_manager.create_pool("demo_pool", "/tmp/demo_pool")
        zfs_manager.create_dataset("demo_pool", "demo_dataset")
        print("✅ Demo ZFS pool + dataset created")

    except Exception as e:
        print(f"Demo setup warning: {e}")

    print("🚀 Startup sequence complete (check /ws for events)")


# ---------------------------------------------------------------------
#                      STARTUP EVENTS
# ---------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    When backend starts:
      - Start monitoring broadcast
      - Run demo initialization
    """
    asyncio.create_task(periodic_broadcast(5.0))
    asyncio.create_task(demo_sequence())
    print("✅ Monitoring + demo initialized.")


# ---------------------------------------------------------------------
#                      MAIN ENTRY POINT
# ---------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("run_nas:app", host="0.0.0.0", port=8000, reload=False)
