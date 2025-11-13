"""
backend/app/main.py
-------------------
Main FastAPI entrypoint for the MyNAS backend.
Integrates:
 - REST API routes
 - RPC handlers
 - WebSocket realtime system
 - Monitoring broadcaster
 - Plugin auto-loader
"""
import uvicorn
import asyncio
import logging
from fastapi import FastAPI , WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Import backend modules ---

from backend.app.config_manager import ConfigManager
from backend.api.zfs import list_pools,create_dataset_api,list_datasets_api
from backend.api import storage, shares, backup, network, monitoring, compat
#from backend.app.plugin_manager import PluginManager
from backend.realtime.websocket_server import WSManager, WSManagerProxy
from backend.storage.storage_manager import detect_disks, list_filesystems, list_pools , disk_info
from backend.storage.zfs_manager import list_datasets_api
from backend.storage.share_manager import load_shares
from backend.app.monitoring import periodic_broadcast

# --- REST API routers ---
from backend.api import (
    storage,
    shares,
    users,
    acl,
    zfs,
    backup,
    #monitoring,
    network,
)

# --- RPC Dispatcher ---
from backend.rpc_handlers.rpc_server import (
    router as rpc_router,
    auto_register as load_rpc_modules,
)

logger = logging.getLogger("mynas.main")
logger.setLevel(logging.INFO)

app = FastAPI(title="MyNAS")

# CORS - allow local dev; lock down for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config manager & global ws manager

ws_manager = WSManager()
WSManagerProxy.register(ws_manager)





# Include API router
app.include_router(zfs.router, prefix="/api/zfs", tags=["ZFS"])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(acl.router, prefix="/api/acl", tags=["Acl"])
app.include_router(shares.router, prefix="/api/shares", tags=["Shares"])
app.include_router(backup.router, prefix="/api/backup", tags=["Backup"])
app.include_router(network.router, prefix="/api/network", tags=["Network"])
#app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(compat.router, prefix="/api", tags=["CompatRPC"])
app.include_router(rpc_router, prefix="/api", tags=["RPC"])






# --- Include RPC router ---


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for realtime events to Flutter/UI clients."""
    await ws_manager.connect(ws)
    logger.info(f"WebSocket connected: {ws.client}")
    try:
        while True:
            data = await ws.receive_text()
            # Optional: handle incoming WS commands (e.g., ping)
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(ws)
        logger.info(f"WebSocket disconnected: {ws.client}")

# --- Root route ---
@app.get("/")
async def root():
    """Basic status check."""
    return JSONResponse(
        {
            "status": "running",
            "version": app.version,
            "message": "MyNAS backend API operational",
        }
    )        

# ------------------------------------------------------------------------------
# 🧩 Startup & Shutdown Events
# ------------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("=== Starting MyNAS backend services ===")
    cfg = ConfigManager()
    cfg.ensure_initialized()

       # 2️⃣ Initialize core storage system
    detect_disks()
    pools = list_pools()
    dataset = list_datasets_api()
    logger.info(f"✅ Detected ZFS pools: {pools}")

    # 3️⃣ Load existing shares (SMB/NFS)
    load_shares()
    logger.info("✅ Shares loaded successfully.")

    # 1️⃣ Load backend plugins
    #load_plugins()
    #logger.info("✅ Plugins loaded")
    

    # 2️⃣ Load RPC handler modules
    load_rpc_modules()
    logger.info("✅ RPC handlers registered")

    # 3️⃣ Register WebSocket manager globally
    WSManagerProxy.register(ws_manager)
    logger.info("✅ WebSocket manager configured")

    # 4️⃣ Start monitoring broadcast loop
    #loop = asyncio.get_event_loop()
    #periodic_broadcast(loop)
    #logger.info("✅ Monitoring started (5s interval)")

    logger.info("=== Backend startup complete ===")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 MyNAS Backend Shutting down...")

# --- Run server (if directly executed) ---
if __name__ == "__main__":
     uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
    
