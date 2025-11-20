#!/usr/bin/env python3
"""
backend/run_backend.py
----------------------
Final optimized unified launcher for MyNAS backend + Flutter Web frontend.

Features:
 - Initializes backend (RPC handlers, WS manager)
 - Auto-detects flutter project (checks /mynas, /root/mynas and nested pubspec.yaml)
 - Detects local IP automatically
 - Starts Flutter Web (default: --release for fast startup)
 - Watches Flutter stdout and opens browser once serving
 - Launches FastAPI via uvicorn
 - Graceful shutdown and logging
Usage:
    python backend/run_backend.py
    python backend/run_backend.py --port 8000 --reload --flutter-mode release
"""

import argparse
import asyncio
import logging
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import uvicorn

# --- Backend imports (may raise if modules missing) ---
from backend.app.main import app, ws_manager
from backend.rpc_handlers.rpc_server import auto_register as load_rpc_modules
from backend.realtime.websocket_server import WSManagerProxy

# -----------------------
# Logging setup
# -----------------------
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "config" / "logs"
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

# -----------------------
# Utility functions
# -----------------------
def get_local_ip() -> str:
    """Return the most likely local network IP address (not 127.0.0.1)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't send traffic; used to pick the default interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def ensure_flutter_web_support_interactive(flutter_path: Path):
    """
    If Flutter web folder missing, ask user whether to create it.
    If yes → run flutter create .
    If no → skip and continue.
    """

    web_dir = flutter_path / "web"
    pubspec = flutter_path / "pubspec.yaml"

    # Not a valid flutter project
    if not pubspec.exists():
        print(f"❌ pubspec.yaml missing → invalid Flutter project: {flutter_path}")
        return True   # allow backend to continue, but flutter will fail

    # Web folder already exists → OK
    if web_dir.exists():
        print("✔ Flutter web folder already exists.")
        return True

    # Ask user
    print("⚠️ Flutter web folder is missing.")
    print(f"Project: {flutter_path}")
    choice = input("👉 Create Flutter web folder now? (y/n): ").strip().lower()

    if choice != "y":
        print("⏩ Skipped creating web folder. Flutter will run anyway.")
        return True

    # User selected yes
    print("🔧 Running: flutter create . (creating web folder...)")

    try:
        result = subprocess.run(
            ["flutter", "create", "."],
            cwd=str(flutter_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(result.stdout)

        if web_dir.exists():
            print("✔ Web folder created successfully.")
            return True

        print("❌ Failed: web folder still missing after flutter create .")
        return False

    except Exception as e:
        print(f"❌ Error running flutter create .: {e}")
        return False



def find_flutter_project() -> Optional[Path]:
    """
    Try common locations and then a recursive search for pubspec.yaml.
    Checks:
      - /mynas/frontend_flutter
      - /root/mynas/frontend_flutter
      - current workspace relatives
      - recursive search up from this script's parent (fast)
    """
    # Common candidates (based on your environment)
    candidates = [
        Path("/mynas/frontend_flutter"),
        Path("/root/mynas/frontend_flutter"),
        Path.cwd() / "frontend_flutter",
        Path.cwd() / "flutter",
        Path.cwd() / "frontend",
    ]

    for p in candidates:
        if p.exists() and (p / "pubspec.yaml").exists():
            return p.resolve()

    # Search for pubspec.yaml within two levels of repo root (reasonable depth)
    repo_root = Path(__file__).resolve().parents[2]  # e.g. /root/mynas
    if repo_root.exists():
        for p in repo_root.rglob("pubspec.yaml"):
            return p.parent.resolve()

    # As a last resort, search current working directory tree (may be slower)
    for p in Path.cwd().rglob("pubspec.yaml"):
        return p.parent.resolve()

    return None


# -----------------------
# Backend initialization
# -----------------------
async def initialize_system():
    """Initialize backend subsystems: RPC handlers, WS manager, plugins (if any)."""
    logger.info("Initializing MyNAS backend system...")
    # Load RPC handlers
    try:
         # Load backend plugins
         # load_plugins()
         #logger.info("Plugins loaded successfully.")
        load_rpc_modules()
        logger.info("RPC handlers loaded successfully.")
    except Exception as e:
        logger.exception("Failed to load RPC handlers: %s", e)

    # Register WebSocket manager
    try:
        WSManagerProxy.register(ws_manager)
        logger.info("WebSocket manager registered.")
    except Exception as e:
        logger.exception("Failed to register WS manager: %s", e)

    # Start monitoring broadcast
    #loop = asyncio.get_event_loop()
    #periodic_broadcast()
    #logger.info("Monitoring loop started (interval=5s).")
    
    logger.info("Backend initialization completed.")


# -----------------------
# Flutter runner + watcher
# -----------------------
class FlutterRunner:
    def __init__(self, project_path: Path, hostname: str, port: int, mode: str = "profile"):
        self.project_path = project_path
        self.hostname = hostname
        self.port = port
        self.mode = mode  # 'profile' | 'release' | 'debug'
        self.proc: Optional[subprocess.Popen] = None
        self._browser_opened = threading.Event()
        self._stop_requested = threading.Event()

    def _build_cmd(self):
        cmd = [
            "flutter",
            "run",
            "-d",
            "web-server",
            "--web-hostname",
            self.hostname,
            "--web-port",
            str(self.port),
        ]
        if self.mode and self.mode != "debug":
            cmd.insert(len(cmd), f"--{self.mode}")  # insert mode option before hostname/port
        return cmd

    def start(self):
        """Start flutter process and monitoring thread."""
        if not (self.project_path.exists() and (self.project_path / "pubspec.yaml").exists()):
            logger.error("Flutter project missing or invalid: %s", self.project_path)
            return

        logger.info("Starting Flutter: %s (mode=%s) at %s:%s", self.project_path, self.mode, self.hostname, self.port)
        # Change working dir to flutter project
        self._cwd = str(self.project_path)
        cmd = self._build_cmd()

        try:
            self.proc = subprocess.Popen(cmd, cwd=self._cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        except FileNotFoundError:
            logger.error("Flutter executable not found. Make sure 'flutter' is in PATH.")
            return
        except Exception as e:
            logger.exception("Failed to start flutter: %s", e)
            return

        self._monitor_thread = threading.Thread(target=self._monitor_stdout, daemon=True)
        self._monitor_thread.start()

    def _monitor_stdout(self):
        """Read Flutter stdout line-by-line, print it, and open browser when ready."""
        assert self.proc is not None
        url = f"http://{self.hostname}:{self.port}"
        try:
            while True:
                if self.proc.stdout is None:
                    break
                line = self.proc.stdout.readline()
                if line == "" and self.proc.poll() is not None:
                    break
                if not line:
                    # small sleep to avoid busy loop if no data
                    time.sleep(0.1)
                    continue
                # Print flutter output directly
                sys.stdout.write(line)
                sys.stdout.flush()

                # Detect readiness strings used by flutter web-server
                lowered = line.strip().lower()
                ready_triggers = [
                    "running at",    # e.g. "Running at: http://..."
                    "serving",       # "Serving ..."
                    "compiled",      # "Compiled successfully"
                    "built",         # "Built"
                    "listening on",  # sometimes used
                    "listening at"
                ]
                if any(tok in lowered for tok in ready_triggers) and not self._browser_opened.is_set():
                    try:
                        # give a small delay to ensure server is reachable
                        time.sleep(0.4)
                        import webbrowser
                        logger.info("Flutter appears ready — opening browser at %s", url)
                        webbrowser.open(url)
                        self._browser_opened.set()
                    except Exception:
                        logger.exception("Failed to open browser")
                if self._stop_requested.is_set():
                    break
        except Exception as e:
            logger.exception("Error while monitoring flutter stdout: %s", e)

    def stop(self, timeout: float = 5.0):
        """Stop flutter process."""
        self._stop_requested.set()
        if self.proc is None:
            return
        try:
            logger.info("Stopping Flutter process (pid=%s)...", getattr(self.proc, "pid", None))
            # try graceful terminate
            self.proc.terminate()
            try:
                self.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                logger.warning("Flutter did not stop in time; killing...")
                self.proc.kill()
        except Exception as e:
            logger.exception("Error stopping Flutter: %s", e)


# -----------------------
# Main launcher
# -----------------------
def main():
    parser = argparse.ArgumentParser(description="MyNAS Backend Server (with optional Flutter auto-run)")
    parser.add_argument("--host", default="0.0.0.0", help="API host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable autoreload for backend (dev)")
    parser.add_argument("--log-level", default="info", help="Logging level (debug/info/warning/error)")
    parser.add_argument("--flutter-mode", default="profile", choices=["release", "profile", "debug"], help="Flutter run mode (default: profile for fastest startup)")
    parser.add_argument("--flutter-port", type=int, default=8084, help="Flutter web server port (default: 8084)")
    parser.add_argument("--flutter-hostname", default=None, help="Flutter hostname to bind (auto-detect if not provided)")
    parser.add_argument("--no-flutter", action="store_true", help="Do not start Flutter automatically")
    args = parser.parse_args()

    # set logging level
    logging.getLogger().setLevel(args.log_level.upper())

    # print header
    print("=" * 60)
    print("🚀 Starting MyNAS Full Stack (Backend + optional Flutter Web)")
    print(f"→ Backend: http://{args.host}:{args.port}")
    print(f"→ Logs:    {LOG_FILE}")
    if not args.no_flutter:
        print(f"→ Flutter mode: {args.flutter_mode}, port: {args.flutter_port}")
    print("=" * 60)

    # initialize backend systems (sync)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_system())

    flutter_path = find_flutter_project()

    if flutter_path:
    # Ask user whether to create web folder
       if ensure_flutter_web_support_interactive(flutter_path):
         ip = get_local_ip()
         flutter_runner = FlutterRunner(flutter_path, ip, args.flutter_port, args.flutter_mode)
         flutter_runner.start()
       else:
         logger.error("Flutter Web setup failed. Skipping Flutter startup.")
    else:
     logger.warning("Flutter project not found. Flutter will not run.")

  

    # Run uvicorn (blocking)
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
        logger.info("KeyboardInterrupt received — shutting down.")
    except Exception as e:
        logger.exception("Uvicorn crashed: %s", e)
    finally:
        # stop flutter if running
        if flutter_runner is not None:
            flutter_runner.stop()
            # give a short moment for shutdown
            time.sleep(0.5)
        logger.info("Backend terminated. Goodbye.")


if __name__ == "__main__":
    main()
