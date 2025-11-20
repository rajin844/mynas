# frontend/cli.py
import asyncio
import json
import websockets
import socket
import argparse
import signal

def get_server_ip():
    """Auto detect server LAN IP via default route."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

async def ws_listener(ws):
    while True:
        try:
            msg = await ws.recv()
            print(f"\n[WS] {msg}")
            print("> ", end="", flush=True)
        except:
            print("WS disconnected.")
            return

async def ws_sender(ws):
    while True:
        cmd = await asyncio.to_thread(input, "> ")
        if cmd.strip() == "exit":
            await ws.close()
            return
        await ws.send(json.dumps({"command": cmd}))

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", default=6789)
    args = parser.parse_args()

    host = args.host or get_server_ip()
    port = args.port

    uri = f"ws://{host}:{port}/ws"
    print(f"Connecting to: {uri}")

    try:
        async with websockets.connect(uri) as ws:
            print("✔ Connected to WebSocket.")
            listener = asyncio.create_task(ws_listener(ws))
            sender = asyncio.create_task(ws_sender(ws))
            await asyncio.gather(listener, sender)
    except Exception as e:
        print("❌ Failed to connect:", e)

if __name__ == "__main__":
    asyncio.run(main())
