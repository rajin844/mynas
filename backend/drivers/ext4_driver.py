# backend/drivers/ext4_driver.py
import subprocess, json
from typing import List, Dict, Any, Optional
from backend.drivers.storage_driver import StorageDriver
from backend.app.config_manager import cfg

class Ext4Driver(StorageDriver):
    def __init__(self):
        self.cfg = cfg

    def _run(self, cmd):
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return {"rc": p.returncode, "out": p.stdout, "err": p.stderr}
        except Exception as e:
            return {"rc":1, "out":"", "err": str(e)}

    def list_disks(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["lsblk","-J","-o","NAME,KNAME,SIZE,MODEL,ROTA,MOUNTPOINT,TYPE"]).decode()
            j = json.loads(out)
            disks=[]
            for d in j.get("blockdevices", []):
                if d.get("type")=="disk":
                    disks.append({
                        "name": d.get("name"),
                        "devpath": "/dev/" + d.get("kname"),
                        "size": d.get("size"),
                        "model": d.get("model"),
                        "rotational": bool(d.get("rota")),
                        "mountpoint": d.get("mountpoint")
                    })
            return disks
        except Exception:
            return self.cfg.get_section("disks") or []

    # EXT4 driver doesn't support zfs pools; provide minimal metadata operations via cfg
    def list_pools(self):
        return self.cfg.get_storage().get("pools", [])

    def create_pool(self, name: str, layout: Dict[str, Any], dry_run: bool=False):
        # For ext4 "pool" may be mountpoint + device(s). We'll create filesystem on single device.
        devices = layout.get("devices", [])
        if not devices:
            return {"error": "no devices provided"}
        dev = devices[0]
        if dry_run:
            return {"dry_run": True, "cmd_preview": ["mkfs.ext4","-F", dev]}
        res = self._run(["mkfs.ext4","-F", dev])
        if res["rc"] != 0:
            return {"created": False, "error": res["err"]}
        # persist metadata in cfg
        storage = self.cfg.get_storage()
        pools = storage.get("pools", [])
        pools.append({"name": name, "type":"ext4", "devices": devices})
        self.cfg.update_storage({"pools": pools, "datasets": storage.get("datasets", [])})
        return {"created": True}

    def destroy_pool(self, name: str, force: bool=False):
        storage = self.cfg.get_storage()
        pools = [p for p in storage.get("pools", []) if p.get("name")!=name]
        self.cfg.update_storage({"pools": pools, "datasets": storage.get("datasets", [])})
        return {"deleted": True}

    def list_datasets(self, pool: Optional[str]=None):
        return self.cfg.get_storage().get("datasets", [])

    def create_dataset(self, pool: str, name: str, mountpoint: Optional[str]=None):
        storage = self.cfg.get_storage()
        datasets = storage.get("datasets", [])
        datasets.append({"pool": pool, "name": name, "mountpoint": mountpoint})
        self.cfg.update_storage({"pools": storage.get("pools", []), "datasets": datasets})
        return {"created": True}

    def destroy_dataset(self, pool: str, name: str, recursive: bool=False):
        storage = self.cfg.get_storage()
        datasets = [d for d in storage.get("datasets", []) if not (d.get("pool")==pool and d.get("name")==name)]
        self.cfg.update_storage({"pools": storage.get("pools", []), "datasets": datasets})
        return {"deleted": True}

    def list_snapshots(self, pool: Optional[str]=None): return []
    def create_snapshot(self, dataset: str, snapshot_name: str): return {"error":"not_supported"}
    def destroy_snapshot(self, snapshot: str): return {"error":"not_supported"}

    def list_shares(self): return self.cfg.list_shares()
    def create_share(self, meta): self.cfg.add_share(meta); return {"created": True}
    def delete_share(self,name): self.cfg.remove_share(name); return {"deleted": True}

    def list_acls(self, path): return [a for a in self.cfg.list_acls() if a.get("path")==path]
    def set_acl(self, path, acl): self.cfg.set_section("acl", [a for a in self.cfg.list_acls() if a.get("path")!=path] + [{"path": path, "user": e["username"], "permissions": e["permissions"]} for e in acl]); return {"updated": True}
    def remove_acl(self, path, username): self.cfg.remove_acl(path, username); return {"removed": True}
    def smart_health(self, devpath): 
        try:
            p = subprocess.run(["smartctl","-a","-j", devpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0: return {"error": p.stderr}
            return json.loads(p.stdout)
        except Exception as e: return {"error": str(e)}
    def ping(self): return {"ok": True, "driver":"ext4"}
