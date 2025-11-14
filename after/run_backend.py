"""
backend/run_backend.py
----------------------
Unified launcher for the MyNAS backend.

Starts:
 - FastAPI application (from app.main)
 - WebSocket server
 - Plugin system
 - RPC handlers
 - Monitoring broadcaster

Usage:
    python run_backend.py
    python run_backend.py --port 8080 --reload
"""

import sys
import argparse
import asyncio
import logging
import uvicorn
from pathlib import Path
import subprocess
import threading
import os
# --- Import app core ---
from backend.app.main import app, ws_manager
#from backend.app.plugin_manager import load_all as load_plugins
#from backend.app.monitoring import periodic_broadcast
from backend.rpc_handlers.rpc_server import auto_register as load_rpc_modules
from backend.realtime.websocket_server import WSManagerProxy

# --- Setup logging ---
LOG_DIR = Path(__file__).resolve().parent / "config" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "backend.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("mynas.run_backend")

def get_flutter_path():
    """
    Detect correct Flutter path for both:
    - VS Code workspace (/mynas)
    - Ubuntu real path (/root/mynas)
    """
    # Folder if running inside VS Code / Dev-Container
    vscode_path = Path("/mynas/frontend_flutter")

    # Folder if running normally on Ubuntu
    ubuntu_path = Path("/root/mynas/frontend_flutter")

    # Auto-detect based on existence
    if vscode_path.exists() and (vscode_path / "pubspec.yaml").exists():
        return vscode_path

    if ubuntu_path.exists() and (ubuntu_path / "pubspec.yaml").exists():
        return ubuntu_path

    return None

def run_flutter():
    flutter_project = get_flutter_path()

    if flutter_project is None:
        print("❌ Flutter project not found at /mynas or /root/mynas")
        return

    print("🔵 Flutter project found:", flutter_project)

    os.chdir(str(flutter_project))

    cmd = [
        "flutter", "run",
        "-d", "web-server"
    ]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Flutter stopped by user.")



async def initialize_system():
    """Initialize plugins, RPC handlers, and monitoring."""
    logger.info("Initializing MyNAS backend system...")

    # Load backend plugins
   # load_plugins()
    #logger.info("Plugins loaded successfully.")

    # Load RPC handlers
    load_rpc_modules()
    logger.info("RPC handlers registered successfully.")

    # Register WebSocket manager globally
    WSManagerProxy.register(ws_manager)
    logger.info("WebSocket manager registered.")

    # Start monitoring broadcast
    #loop = asyncio.get_event_loop()
    #periodic_broadcast()
    #logger.info("Monitoring loop started (interval=5s).")

    logger.info("MyNAS backend initialized successfully.")


def main():
    """Main launcher entrypoint."""
    parser = argparse.ArgumentParser(description="MyNAS Backend Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run API (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable autoreload for development")
    parser.add_argument("--log-level", default="info", help="Logging level")
    args = parser.parse_args()

    # Setup logging level
    logging.getLogger().setLevel(args.log_level.upper())

    # Print startup header
    print("=" * 60)
    print("🚀 Starting MyNAS Backend Server")
    print(f"→ Host: {args.host}:{args.port}")
    print(f"→ Log:  {LOG_FILE}")
    print("=" * 60)

     # Launch Flutter in a parallel thread
    flutter_thread = threading.Thread(target=run_flutter, daemon=True)
    flutter_thread.start()


    # Run initialization before starting FastAPI
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_system())

    # Run FastAPI using uvicorn
    try:
        uvicorn.run(
            "backend.app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            lifespan="on",
        )
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down gracefully...")
    except Exception as e:
        logger.error(f"Server crash: {e}")
    finally:
        logger.info("Backend terminated.")


if __name__ == "__main__":
    main()
