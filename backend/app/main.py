"""
backend/app/main.py
Clean version WITHOUT ConfigManager (MySQL only)
"""

import uvicorn
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.drivers.db import init_pool


from backend.realtime.websocket_server import WSManager, WSManagerProxy
from backend.storage.storage_manager import detect_disks, list_disks
from backend.storage.zfs_manager import list_pools, list_datasets
from backend.storage.share_manager import load_shares
from backend.app.monitor_broadcaster import periodic_monitor

# REST routers
from backend.api import (
    zfs,
    storage,
    users,
    acl,
    shares,
    backup,
    network,
    compat,
    smart,
    raidz,
    system,
)

# RPC system
from backend.rpc_handlers.rpc_server import router as rpc_router, auto_register as rpc_auto_register

logger = logging.getLogger("mynas.main")
logger.setLevel(logging.INFO)

# FastAPI app
app = FastAPI(title="MyNAS Backend API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global WebSocket manager
ws_manager = WSManager()
WSManagerProxy.register(ws_manager)

# ---------------------------------------------------------
# Include REST Routers
# ---------------------------------------------------------
app.include_router(zfs.router, prefix="/api/zfs", tags=["ZFS"])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(acl.router, prefix="/api/acl", tags=["ACL"])
app.include_router(shares.router, prefix="/api/shares", tags=["Shares"])
app.include_router(backup.router, prefix="/api/backup", tags=["Backup"])
app.include_router(network.router, prefix="/api/network", tags=["Network"])
app.include_router(smart.router, prefix="/api/smart", tags=["SMART"])
app.include_router(raidz.router, prefix="/api/raidz", tags=["RAIDZ"])
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(compat.router, prefix="/api", tags=["Compat"])
app.include_router(rpc_router, prefix="/api/rpc", tags=["RPC"])


# ---------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    logger.info(f"WebSocket connected: {ws.client}")

    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(ws)
        logger.info(f"WebSocket disconnected: {ws.client}")


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------
@app.get("/")
async def root():
    return JSONResponse({
        "status": "running",
        "version": app.version,
        "message": "MyNAS backend operational (MySQL mode)"
    })


# ---------------------------------------------------------
# Startup
# ---------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("=== Starting MyNAS MySQL-based backend ===")

    # Monitoring loop
    asyncio.get_event_loop().create_task(periodic_monitor())
    logger.info("✓ Monitoring broadcaster started")
    await init_pool(
        host="127.0.0.1",
        port=3306,
        user="mynas",
        password="Admin@1234",
        db="mynas",
        minsize=1,
        maxsize=10
    )
    logger.info("✓ MySQL pool ready")

    # Detect disks
    await detect_disks()
    disks = await list_disks()
    logger.info(f"✓ Physical disks: {len(disks)} detected")

    # Load ZFS pools + datasets
    pools =  await list_pools()
    datasets = await list_datasets()
    logger.info(f"✓ ZFS pools loaded: {len(pools)}, datasets: {len(datasets)}")

    # Load shares
    load_shares()
    logger.info(f"✓ shares loaded:")

    # Load ALL RPC handlers
    rpc_auto_register()
    logger.info("✓ RPC handlers auto-registered")

    # WebSocket ready
    WSManagerProxy.register(ws_manager)

    logger.info("=== Backend startup COMPLETE (MySQL mode) ===")


# ---------------------------------------------------------
# Shutdown
# ---------------------------------------------------------
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down MyNAS backend")


# ---------------------------------------------------------
# Run directly
# ---------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
