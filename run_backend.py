#!/usr/bin/env python3
"""
backend/run_backend.py
----------------------
Unified launcher for MyNAS backend + Flutter Web.

✔ Loads backend (FastAPI, RPC handlers, WS manager)
✔ Detects Flutter project automatically
✔ Generates 'web/' folder if missing
✔ Lets user choose Flutter mode (debug/profile/release)
✔ Starts Flutter Web and auto-opens browser
✔ Starts FastAPI backend via uvicorn
✔ Graceful shutdown and safe logging
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

# Backend core
from backend.app.main import app, ws_manager
from backend.rpc_handlers.rpc_server import auto_register as load_rpc_modules
from backend.realtime.websocket_server import WSManagerProxy


# =====================================================================================
# Logging Setup
# =====================================================================================
BASE_DIR = Path(__file__).resolve().parent

logger = logging.getLogger("mynas.run_backend")
logging.basicConfig(level=logging.INFO)


# =====================================================================================
# Utility: Local IP detection
# =====================================================================================
def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# =====================================================================================
# Flutter: Ensure web folder exists
# =====================================================================================
def ensure_flutter_web(flutter_path: Path) -> bool:
    web_dir = flutter_path / "web"
    pubspec = flutter_path / "pubspec.yaml"

    if not pubspec.exists():
        print(f"❌ pubspec.yaml missing at: {flutter_path}")
        return False

    if web_dir.exists():
        print("✔ Flutter 'web/' folder OK.")
        return True

    print("⚠️ Flutter 'web/' missing — creating it…")

    try:
        result = subprocess.run(
            ["flutter", "create", "."],
            cwd=str(flutter_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(result.stdout)
    except Exception as e:
        print("❌ Failed to create Flutter web folder:", e)
        return False

    return web_dir.exists()


# =====================================================================================
# Flutter: Choose mode interactively
# =====================================================================================
def choose_flutter_mode():
    print("\n⚙️  Flutter Web kis mode me chalana hai?")
    print("  1) debug")
    print("  2) profile  (recommended)")
    print("  3) release  (fastest)")

    choice = input("\n👉 Enter choice (1/2/3): ").strip()

    if choice == "1": return "debug"
    if choice == "2": return "profile"
    if choice == "3": return "release"

    print("⚠️ Invalid choice, using 'profile'")
    return "profile"


# =====================================================================================
# Flutter Project Scanner
# =====================================================================================
def find_flutter_project() -> Optional[Path]:
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

    repo_root = Path(__file__).resolve().parents[2]
    if repo_root.exists():
        for p in repo_root.rglob("pubspec.yaml"):
            return p.parent.resolve()

    for p in Path.cwd().rglob("pubspec.yaml"):
        return p.parent.resolve()

    return None


# =====================================================================================
# Backend Initialization
# =====================================================================================
async def initialize_system():
    logger.info("🔧 Initializing MyNAS Backend…")

    try:
        load_rpc_modules()
        logger.info("✓ RPC handlers loaded")
    except Exception as e:
        logger.exception("❌ RPC handler loading failed: %s", e)

    try:
        WSManagerProxy.register(ws_manager)
        logger.info("✓ WS Manager registered")
    except Exception as e:
        logger.exception("❌ WS Manager registration failed: %s", e)

    logger.info("🚀 Backend initialization complete")


# =====================================================================================
# Flutter Runner
# =====================================================================================
class FlutterRunner:
    def __init__(self, path: Path, host: str, port: int, mode: str):
        self.path = path
        self.host = host
        self.port = port
        self.mode = mode
        self.proc = None
        self._browser_open = False
        self._stop = False

    def build_cmd(self):
        return [
            "flutter", "run",
            "-d", "web-server",
            "--web-hostname", self.host,
            "--web-port", str(self.port),
            f"--{self.mode}"
        ]

    def start(self):
        os.chdir(str(self.path))
        cmd = self.build_cmd()

        print(f"\n🚀 Starting Flutter Web ({self.mode}) at http://{self.host}:{self.port}")
        print("📁 Project:", self.path)

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except Exception as e:
            logger.exception("❌ Failed to start Flutter: %s", e)
            return

        threading.Thread(target=self._monitor, daemon=True).start()

    def _monitor(self):
        url = f"http://{self.host}:{self.port}"

        try:
            while True:
                if self.proc.stdout is None:
                    break

                line = self.proc.stdout.readline()
                if not line:
                    if self.proc.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue

                sys.stdout.write(line)
                sys.stdout.flush()

                lowered = line.lower()
                triggers = ["running at", "serving", "built", "compiled", "listening"]

                if not self._browser_open and any(t in lowered for t in triggers):
                    time.sleep(0.6)
                    import webbrowser
                    webbrowser.open(url)
                    self._browser_open = True
                    print(f"\n🌐 Browser opened: {url}")

                if self._stop:
                    break

        except Exception as e:
            logger.exception("Flutter monitor crashed: %s", e)

    def stop(self):
        self._stop = True
        if self.proc:
            try:
                self.proc.terminate()
                time.sleep(0.4)
                self.proc.kill()
            except:
                pass


# =====================================================================================
# Main Launcher
# =====================================================================================
def main():
    parser = argparse.ArgumentParser(description="MyNAS Backend + Flutter Launcher")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--log-level", default="info")
    parser.add_argument("--flutter-mode", default=None)
    parser.add_argument("--no-flutter", action="store_true")
    parser.add_argument("--flutter-port", type=int, default=8084)
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level.upper())

    print("=" * 60)
    print("🚀 Starting MyNAS (Backend + Flutter Web)")
    print(f"→ Backend    : http://{args.host}:{args.port}")
    if not args.no_flutter:
        print(f"→ Flutter    : port {args.flutter_port}")
    print("=" * 60)

    # Backend Initialization
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_system())

    flutter_runner = None

    # Start Flutter if enabled
    if not args.no_flutter:
        flutter_path = find_flutter_project()
        if not flutter_path:
            logger.error("❌ Flutter project not found")
            return

        if not ensure_flutter_web(flutter_path):
            logger.error("❌ Flutter 'web/' folder missing and could not be created")
            return

        chosen_mode = args.flutter_mode or choose_flutter_mode()
        ip = get_local_ip()

        flutter_runner = FlutterRunner(flutter_path, ip, args.flutter_port, chosen_mode)
        flutter_runner.start()

    # Start FastAPI Backend
    try:
        uvicorn.run(
            "backend.app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
        )
    finally:
        if flutter_runner:
            flutter_runner.stop()
        print("🛑 Backend stopped.")


if __name__ == "__main__":
    main()
