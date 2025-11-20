# backend/app/drivers/zfs_driver.py
import subprocess, os
from typing import List, Dict, Any, Optional
from backend.app.storage_driver import StorageDriver
from backend.app.config_manager import cfg
class ZFSStorageDriver(StorageDriver):
    # backend/drivers/zfs_driver.py
    #class ZFSDriver(StorageDriver):

    def __init__(self):
        self.cfg = cfg

    def _run(self, cmd: List[str]) -> Dict[str, Any]:
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return {"rc": p.returncode, "out": p.stdout, "err": p.stderr}
        except Exception as e:
            return {"rc": 1, "out": "", "err": str(e)}

    def list_pools(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["zpool","list","-H","-o","name,size,health"]).decode()
            rows=[]
            for l in out.splitlines():
                parts = l.split()
                rows.append({"name": parts[0], "size": parts[1] if len(parts)>1 else None, "health": parts[2] if len(parts)>2 else "UNKNOWN"})
            return rows
        except Exception:
            return self.cfg.get_storage().get("pools", [])   

    
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
    

    def create_pool(self, name: str, layout: Dict[str, Any], dry_run: bool=False) -> Dict[str, Any]:
        t = layout.get("type","single")
        devs = layout.get("devices", [])
        if dry_run:
            cmd = ["zpool","create","-n", name]
        else:
            cmd = ["zpool","create","-f", name]

        if t == "single":
            cmd += devs
        elif t == "mirror":
            cmd += ["mirror"] + devs
        elif t.startswith("raidz"):
            cmd += [t] + devs
        else:
            cmd += devs

        if dry_run:
            return {"dry_run": True, "cmd_preview": cmd}
        res = self._run(cmd)
        if res["rc"] != 0:
            return {"created": False, "error": res["err"]}
        # persist metadata into config for visibility (driver optional)
        storage = self.cfg.get_storage()
        pools = storage.get("pools", [])
        pools.append({"name": name, "type": "zfs", "devices": devs})
        self.cfg.update_storage({"pools": pools, "datasets": storage.get("datasets", [])})
        return {"created": True, "pool": name}

    
    def destroy_pool(self, name: str, force: bool=False) -> Dict[str, Any]:
        res = self._run(["zpool","destroy","-f", name])
        if res["rc"] != 0:
            return {"deleted": False, "error": res["err"]}
        storage = self.cfg.get_storage()
        pools = [p for p in storage.get("pools", []) if p.get("name")!=name]
        self.cfg.update_storage({"pools": pools, "datasets": storage.get("datasets", [])})
        return {"deleted": True}

    def zcreate_pool(self, name, devices: List[str], **opts):
        raidz = opts.get("raidz")
        dry_run = opts.get("dry_run", True)
        normalized = [d if d.startswith("/dev/") else "/dev/" + d for d in devices]
        not_found = [d for d in normalized if not os.path.exists(d)]
        if not_found:
            return {"created": False, "error": f"devices not found: {not_found}"}

        # build zpool create
        cmd = ["zpool","create","-f",name]
        if raidz and raidz in ("raidz1","raidz2","raidz3","mirror","single"):
            if raidz == "single":
                cmd += normalized
            elif raidz == "mirror":
                cmd += ["mirror"] + normalized
            else:
                cmd += [raidz] + normalized
        else:
            cmd += normalized

        if dry_run:
            return {"dry_run": True, "cmd": cmd}

        if os.geteuid() != 0:
            return {"created": False, "error": "requires root"}

        res = self._run(cmd)
        if res["rc"] != 0:
            return {"created": False, "error": res["err"], "cmd": cmd}

        # persist metadata
        driverdb.save_pool({"name": name, "type": "zfs", "devices": normalized, "raidz": raidz})
        return {"created": True, "pool": name, "cmd": cmd}

    def zdestroy_pool(self, name):
        if os.geteuid() != 0:
            return {"error":"requires root"}
        res = self._run(["zpool","destroy","-f",name])
        if res["rc"] == 0:
            driverdb.remove_pool(name)
        return res


    def list_datasets(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["zfs","list","-H","-o","name,mountpoint"]).decode()
            rows=[]
            for l in out.splitlines():
                name,mount = l.split("\t")
                if pool and not name.startswith(pool + "/"): continue
                rows.append({"name": name, "mountpoint": mount})
            return rows
        except Exception:
            ds = self.cfg.get_storage().get("datasets", [])
            if pool:
                return [d for d in ds if d.get("pool")==pool]
            return ds

   

    def create_dataset(self, pool: str, name: str, mountpoint: Optional[str]=None) -> Dict[str, Any]:
        cmd = ["zfs","create"]
        if mountpoint:
            cmd += ["-o", f"mountpoint={mountpoint}"]
        cmd.append(f"{pool}/{name}")
        res = self._run(cmd)
        if res["rc"] != 0:
            return {"created": False, "error": res["err"]}
        storage = self.cfg.get_storage()
        datasets = storage.get("datasets", [])
        datasets.append({"pool": pool, "name": name, "mountpoint": mountpoint})
        self.cfg.update_storage({"pools": storage.get("pools", []), "datasets": datasets})
        return {"created": True, "dataset": f"{pool}/{name}"}

    def destroy_dataset(self, pool: str, name: str, recursive: bool=False) -> Dict[str, Any]:
        cmd = ["zfs","destroy"]
        if recursive:
            cmd += ["-r"]
        cmd.append(f"{pool}/{name}")
        res = self._run(cmd)
        if res["rc"] != 0:
            return {"deleted": False, "error": res["err"]}
        storage = self.cfg.get_storage()
        datasets = [d for d in storage.get("datasets", []) if not (d.get("pool")==pool and d.get("name")==name)]
        self.cfg.update_storage({"pools": storage.get("pools", []), "datasets": datasets})
        return {"deleted": True}

    def list_snapshots(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["zfs","list","-t","snapshot","-H","-o","name"]).decode()
            rows = [{"name": l.strip()} for l in out.splitlines() if (not pool or l.startswith(pool + "/"))]
            return rows
        except Exception:
            return []

    def create_snapshot(self, dataset: str, snapshot_name: str) -> Dict[str, Any]:
        res = self._run(["zfs","snapshot", f"{dataset}@{snapshot_name}"])
        if res["rc"] != 0:
            return {"created": False, "error": res["err"]}
        return {"created": True}

    def destroy_snapshot(self, snapshot: str) -> Dict[str, Any]:
        res = self._run(["zfs","destroy", snapshot])
        if res["rc"] != 0:
            return {"deleted": False, "error": res["err"]}
        return {"deleted": True}

    def list_shares(self) -> List[Dict[str, Any]]:
        return self.cfg.list_shares()

    def create_share(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        self.cfg.add_share(meta)
        return {"created": True, "share": meta}

    def delete_share(self, name: str) -> Dict[str, Any]:
        self.cfg.remove_share(name)
        return {"deleted": True}

    def list_acls(self, path: str) -> List[Dict[str, Any]]:
        return [a for a in self.cfg.list_acls() if a.get("path")==path]

    def set_acl(self, path: str, acl: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.cfg.set_section("acl", [a for a in self.cfg.list_acls() if a.get("path")!=path] + [{"path": path, "user": e["username"], "permissions": e["permissions"]} for e in acl])
        return {"updated": True}

    def remove_acl(self, path: str, username: str) -> Dict[str, Any]:
        self.cfg.remove_acl(path, username)
        return {"removed": True}

    def smart_health(self, devpath: str) -> Dict[str, Any]:
        try:
            p = subprocess.run(["smartctl","-a","-j", devpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                return {"error": p.stderr}
            return json.loads(p.stdout)
        except Exception as e:
            return {"error": str(e)}

    def ping(self) -> Dict[str, Any]:
        return {"ok": True, "driver": "zfs"}

    
        # ------------------------------------------------------------
    # PROPERTIES + SNAPSHOTS
    # ------------------------------------------------------------
    def get_properties(self, pool, ds):
        return {}  # add later
    
    def set_property(self, pool, ds, prop, value):
        return self._run(["zfs", "set", f"{prop}={value}", f"{pool}/{ds}"])

    def get_properties(self,pool,dataset): return {}
    def set_property(self,pool,dataset,prop,value): return {"error":"not_implemented"}
    
        

