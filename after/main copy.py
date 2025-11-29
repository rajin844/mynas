# backend/app/main.py
import uvicorn
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.realtime.websocket_server import WSManager, WSManagerProxy
from backend.app.monitor_broadcaster import periodic_monitor
from backend.drivers.db import init_db
from backend.rpc_handlers.rpc_server import router as rpc_router, auto_register as rpc_auto_register

# REST Routers
from backend.api import (
    zfs, storage, users, acl, shares, backup, network,
    monitoring as monitoring_api,
    smart as smart_api,
    raidz as raidz_api,
    system as system_api,
    compat,
)

# Storage init
from backend.storage.storage_manager import detect_disks 
from backend.storage.zfs_manager import list_pools, list_datasets
from backend.storage.share_manager import load_shares


logger = logging.getLogger("mynas.main")
logger.setLevel(logging.INFO)

app = FastAPI(title="MyNAS Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

ws_manager = WSManager()
WSManagerProxy.register(ws_manager)

# Routers
app.include_router(zfs.router, prefix="/api/zfs", tags=["ZFS"])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(acl.router, prefix="/api/acl", tags=["ACL"])
app.include_router(shares.router, prefix="/api/shares", tags=["Shares"])
app.include_router(backup.router, prefix="/api/backup", tags=["Backup"])
app.include_router(network.router, prefix="/api/network", tags=["Network"])
app.include_router(monitoring_api.router, prefix="/api/monitor", tags=["Monitoring"])
app.include_router(smart_api.router, prefix="/api/smart", tags=["SMART"])
app.include_router(raidz_api.router, prefix="/api/raidz", tags=["RAIDZ"])
app.include_router(system_api.router, prefix="/api/system", tags=["System"])
app.include_router(compat.router, prefix="/api", tags=["Compat"])
app.include_router(rpc_router, prefix="/api/rpc", tags=["RPC"])


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    logger.info(f"WebSocket connected: {ws.client}")
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(ws)
        logger.info(f"WebSocket disconnected: {ws.client}")

@app.get("/")
async def root():
    return JSONResponse({
        "status": "running",
        "version": app.version,
        "message": "MyNAS backend operational"
    })


# =====================================================================
# STARTUP EVENT
# =====================================================================
@app.on_event("startup")
async def on_startup():

    logger.info("=== MyNAS Backend Startup ===")
    await init_db()
    try:
        rpc_auto_register()
        logger.info("RPC handlers auto-registered")
    except Exception as e:
        logger.exception("RPC auto-register failed: %s", e)

    # 2) Start monitoring broadcaster
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(periodic_monitor())
        logger.info("Monitoring broadcaster scheduled")
    except Exception as e:
        logger.exception("Monitor broadcaster start failed: %s", e)

    # 3) Initialize storage subsystem (best-effort; non-fatal)
    try:
        # detect_disks might be async or sync in your implementation
        try:
            await detect_disks()
        except TypeError:
            detect_disks()

        try:
            pools = await list_pools()
            datasets = await list_datasets()
            logger.info("ZFS pools discovered: %s", [p.get("name") for p in pools])
        except Exception:
            # non-fatal, pools may not be present yet
            logger.debug("ZFS list failed during startup (continuing).")
    except Exception as e:
        logger.exception("Storage initialization error: %s", e)

    # 4) Load shares (best-effort)
    try:
        maybe = load_shares()
        if asyncio.iscoroutine(maybe):
            await maybe
        logger.info("Shares loaded")
    except Exception:
        logger.debug("Shares load failed (continuing).")

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
