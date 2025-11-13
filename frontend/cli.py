#!/usr/bin/env python3
import threading, asyncio, requests, json, time
from websockets import connect

API = API_URL = "http://localhost:8000"

def create_user(u, p):
    r = requests.post(f"{API}/api/users/create", json={"username":u,"password":p,"role":"admin"})
    print(r.json())

def create_pool(name, devices):
    r = requests.post(f"{API}/api/storage/pools/create", json={"name":name,"devices": devices})
    print(r.json())

async def listen_ws():
    uri = "ws://127.0.0.1:8000/ws"
    try:
        async with connect(uri) as ws:
            print("WS connected")
            async for msg in ws:
                print("EVENT:", msg)
    except Exception as e:
        print("WS error:", e)

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(listen_ws()), daemon=True).start()
    time.sleep(0.5)
    print("CLI ready. commands: user <u> <p>, pool <name> <devs...>, exit")
    while True:
        cmd = input("> ").strip()
        if cmd == "exit": break
        parts = cmd.split()
        if not parts: continue
        if parts[0] == "user":
            create_user(parts[1], parts[2])
        elif parts[0] == "pool":
            create_pool(parts[1], parts[2:])
