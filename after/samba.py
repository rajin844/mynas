# backend/app/rpc_handlers/samba.py
import subprocess, os, json
from ..ws_server import notify_clients

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
SHARES_FILE = os.path.join(DATA_DIR,"shares.json")

SAMBA_CONF = "/etc/samba/smb.conf"

def _load_shares():
    if not os.path.exists(SHARES_FILE): return []
    with open(SHARES_FILE) as f: return json.load(f)

def _save_samba_conf():
    shares = _load_shares()
    lines = ["[global]",
             "   workgroup = WORKGROUP",
             "   server string = NAS Server",
             "   map to guest = Bad User",
             "   security = user",
             ""]
    for s in shares:
        path = f"/mnt/{s['dataset']}"
        os.makedirs(path, exist_ok=True)
        lines.append(f"[{s['dataset']}]")
        lines.append(f"   path = {path}")
        lines.append(f"   read only = {'yes' if s.get('readonly', False) else 'no'}")
        lines.append(f"   guest ok = {'yes' if s.get('guest', False) else 'no'}")
        lines.append(f"   create mask = 0775")
        lines.append(f"   directory mask = 0775")
        lines.append("")
    with open(SAMBA_CONF, "w") as f:
        f.write("\n".join(lines))
    subprocess.call(["systemctl","restart","smbd"])
    notify_clients({"module":"shares","action":"samba_update"})

def apply_samba():
    _save_samba_conf()
