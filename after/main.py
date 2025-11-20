import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config_manager import ConfigManager
from backend.app.plugin_manager import PluginManager
from backend.realtime.websocket_server import WSManager
from backend.storage.storage_manager import storage as storage_router, users as users_router, acl as acl_router, backup as backup_router, monitoring as monitoring_router, shares as shares_router, network as network_router
from app.realtime.websocket_server import WSManager, WSManagerProxy
from app.monitoring import MonitoringDaemon


logger = logging.getLogger("mynas")
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

ws = WSManager()
wss= WSManagerProxy()

# Include API routers
app.include_router(users_router.router, prefix="/api/users", tags=["users"])
app.include_router(storage_router.router, prefix="/api/storage", tags=["storage"])
app.include_router(shares_router.router, prefix="/api/shares", tags=["shares"])
app.include_router(acl_router.router, prefix="/api/acl", tags=["acl"])
app.include_router(backup_router.router, prefix="/api/backup", tags=["backup"])
app.include_router(monitoring_router.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(network_router.router, prefix="/api/network", tags=["network"])

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await broadcaster.connect(ws)
    try:
        while True:
            # keep alive and optionally receive client pings
            await ws.receive_text()
    except Exception:
        await broadcaster.disconnect(ws)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting MyNAS backend")
    cfg = ConfigManager()
    cfg.ensure_initialized()
    load_plugins()
    # Start monitoring broadcaster
    from app.realtime.monitoring_agent import start_monitoring_agent
    start_monitoring_agent(ws)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 MyNAS Backend Shutting down...")

@app.get("/")
async def root():
    return {"status": "ok", "service": "mynas backend v8"}
    
app.mount("/ws",WSManager)