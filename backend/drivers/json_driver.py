# backend/drivers/json_driver.py
from backend.drivers.base import StorageDriver
from backend.app.config_manager import cfg
from typing import List, Dict, Any, Optional

class JSONDriver(StorageDriver):
    def __init__(self, cfg_obj):
        self.cfg = cfg_obj

    def list_disks(self) -> List[Dict[str, Any]]:
        # JSON driver cannot detect disks; fallback empty or from config
        return self.cfg.get_section("disks") or []

    def list_pools(self) -> List[Dict[str, Any]]:
        return self.cfg.get_storage().get("pools", [])

    def create_pool(self, name: str, layout: Dict[str, Any], dry_run: bool=False) -> Dict[str, Any]:
        pool = {"name": name, "layout": layout}
        if not dry_run:
            pools = self.cfg.get_storage().get("pools", [])
            pools.append(pool)
            self.cfg.update_storage({"pools": pools, "datasets": self.cfg.get_storage().get("datasets", [])})
            return {"created": True, "pool": pool}
        else:
            return {"dry_run": True, "preview": pool}

    def destroy_pool(self, name: str, force: bool=False) -> Dict[str, Any]:
        pools = [p for p in self.cfg.get_storage().get("pools", []) if p["name"] != name]
        self.cfg.update_storage({"pools": pools, "datasets": self.cfg.get_storage().get("datasets", [])})
        return {"deleted": True}

    def list_datasets(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        ds = self.cfg.get_storage().get("datasets", [])
        if pool:
            return [d for d in ds if d.get("pool")==pool]
        return ds

    def create_dataset(self, pool: str, name: str, mountpoint: Optional[str]=None) -> Dict[str, Any]:
        ds = {"pool": pool, "name": name, "mountpoint": mountpoint}
        datasets = self.cfg.get_storage().get("datasets", [])
        datasets.append(ds)
        self.cfg.update_storage({"pools": self.cfg.get_storage().get("pools", []), "datasets": datasets})
        return {"created": True, "dataset": ds}

    def destroy_dataset(self, pool: str, name: str, recursive: bool=False) -> Dict[str, Any]:
        datasets = [d for d in self.cfg.get_storage().get("datasets", []) if not (d["pool"]==pool and d["name"]==name)]
        self.cfg.update_storage({"pools": self.cfg.get_storage().get("pools", []), "datasets": datasets})
        return {"deleted": True}

    def list_snapshots(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        return []

    def create_snapshot(self, dataset: str, snapshot_name: str) -> Dict[str, Any]:
        return {"error": "not_supported"}

    def destroy_snapshot(self, snapshot: str) -> Dict[str, Any]:
        return {"error": "not_supported"}

    # shares
    def list_shares(self) -> List[Dict[str, Any]]:
        return self.cfg.list_shares()

    def create_share(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        self.cfg.add_share(meta)
        return {"created": True, "share": meta}

    def delete_share(self, name: str) -> Dict[str, Any]:
        self.cfg.remove_share(name)
        return {"deleted": True}

    # ACLs
    def list_acls(self, path: str) -> List[Dict[str, Any]]:
        return [a for a in self.cfg.list_acls() if a.get("path")==path]

    def set_acl(self, path: str, acl: List[Dict[str, Any]]) -> Dict[str, Any]:
        # replace all for path
        orig = [a for a in self.cfg.list_acls() if a.get("path") != path]
        for e in acl:
            orig.append({"path": path, "user": e["username"], "permissions": e["permissions"]})
        self.cfg.set_section("acl", orig)
        return {"updated": True}

    def remove_acl(self, path: str, username: str) -> Dict[str, Any]:
        acls = [a for a in self.cfg.list_acls() if not (a.get("path")==path and a.get("user")==username)]
        self.cfg.set_section("acl", acls)
        return {"removed": True}

    def smart_health(self, devpath: str) -> Dict[str, Any]:
        return {"error":"not_supported"}

    def ping(self) -> Dict[str, Any]:
        return {"ok": True, "backend": "json"}
