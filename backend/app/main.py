"""
backend/app/main.py
-------------------
Main FastAPI entrypoint for the MyNAS backend.

Integrates:
 - REST API routes
 - RPC handlers (auto-loaded)
 - WebSocket realtime system
 - Disk detection / ZFS init
 - Storage / Snapshot / Alerts bootstrap
 - Monitoring broadcaster
"""

import uvicorn
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Core config + base services
from backend.app.config_manager import ConfigManager
from backend.realtime.websocket_server import WSManager, WSManagerProxy
from backend.app.monitor_broadcaster import periodic_monitor
 # API CONFIG FILESAPI
from backend.api import storage
from backend.api import zfs
from backend.api import shares
from backend.api import acl
from backend.api import backup
from backend.api import monitoring
from backend.api import compat
from backend.api import nas
from backend.api import network
from backend.api import system
from backend.api import users
from backend.api import raidz
from backend.api import smart


# Storage boot systems
from backend.storage.storage_manager import detect_disks, list_disks
from backend.storage.zfs_manager import list_pools, list_datasets
from backend.storage.share_manager import load_shares

# REST Routers

# RPC auto-loader
from backend.rpc_handlers.rpc_server import (
    router as rpc_router,
    auto_register as rpc_auto_register,
)

logger = logging.getLogger("mynas.main")
logger.setLevel(logging.INFO)

# =====================================================================
# FASTAPI APP INIT
# =====================================================================
app = FastAPI(title="MyNAS Backend API", version="1.0.0")

# CORS (anywhere allowed for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Global WebSocket manager
ws_manager = WSManager()
WSManagerProxy.register(ws_manager)

# =====================================================================
# REST API ROUTES
# =====================================================================
app.include_router(zfs.router,     prefix="/api/zfs",     tags=["ZFS"])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"])
app.include_router(users.router,   prefix="/api/users",   tags=["Users"])
app.include_router(acl.router,     prefix="/api/acl",     tags=["ACL"])
app.include_router(shares.router,  prefix="/api/shares",  tags=["Shares"])
app.include_router(backup.router,  prefix="/api/backup",  tags=["Backup"])
app.include_router(network.router, prefix="/api/network", tags=["Network"])
app.include_router(monitoring.router, prefix="/api/monitor", tags=["Monitoring"])

# NEW APIs
app.include_router(raidz.router,   prefix="/api/raidz",   tags=["RAIDZ"])
app.include_router(smart.router,   prefix="/api/smart",   tags=["SMART"])
app.include_router(system.router,  prefix="/api/system",  tags=["System"])

# RPC + Compat
app.include_router(compat.router,  prefix="/api",         tags=["Compat"])
app.include_router(rpc_router,     prefix="/api/rpc",     tags=["RPC"])

# =====================================================================
# WEBSOCKET ENDPOINT
# =====================================================================
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    logger.info(f"WS connected: {ws.client}")

    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(ws)
        logger.info(f"WS disconnected: {ws.client}")

# =====================================================================
# ROOT
# =====================================================================
@app.get("/")
async def root():
    return JSONResponse({
        "status": "running",
        "version": app.version,
        "message": "MyNAS backend operational",
    })

# =====================================================================
# STARTUP EVENT
# =====================================================================
@app.on_event("startup")
async def on_startup():
    logger.info("=== MyNAS Backend Startup ===")

    # 1) Start monitoring broadcaster
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_monitor())
    logger.info("✓ Monitoring broadcaster running")

    # 2) Config
    cfg = ConfigManager()
    cfg.ensure_initialized()
    logger.info("✓ Config ready")

    # 3) Disk detection
    detect_disks()
    disks = list_disks()
    logger.info(f"✓ Disks detected: {len(disks)}")

    # 4) ZFS detection
    pools = list_pools()
    datasets = list_datasets()
    logger.info(f"✓ ZFS Loaded: Pools={len(pools)} | Datasets={len(datasets)}")

    # 5) Load SMB/NFS shares
    load_shares()
    logger.info("✓ Shares loaded")

    # 6) Auto-load all RPC handlers
    try:
        rpc_auto_register()
        logger.info("✓ RPC handlers auto-loaded")
    except Exception as e:
        logger.exception("RPC auto-register failed: %s", e)

    # 7) WebSocket system ready
    WSManagerProxy.register(ws_manager)
    logger.info("✓ WebSocket manager registered")

    logger.info("=== Backend startup complete ===")

# =====================================================================
# SHUTDOWN
# =====================================================================
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 Backend shutting down...")

# =====================================================================
# RUN (DIRECT)
# =====================================================================
if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
