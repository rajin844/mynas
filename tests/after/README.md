MyNAS v7 - Full updated backend bundle (prototype)
==================================================
Contents:
- backend/: managers (user, permissions, plugins, backups, monitoring, config)
- storage/: storage management placeholders (zfs, shares, acl, network)
- realtime/: WebSocket manager
- frontend_flutter/: Flutter placeholder UI connected to /ws
- run_nas.py: entrypoint (starts FastAPI, starts monitoring, runs demo)

Quick start:
1. python3 -m venv venv
2. source venv/bin/activate
3. pip install -r requirements.txt
4. python run_nas.py
5. Open ws client: ws://127.0.0.1:8000/ws

Note: This is a prototype. Replace placeholders with real system calls for production.
