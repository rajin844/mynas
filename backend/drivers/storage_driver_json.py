# backend/app/storage_driver_json.py
from typing import List, Dict, Any, Optional
from backend.app.storage_driver import StorageDriver
#from backend.app.driver_persistence import driverdb
from backend.app.config_manager import cfg
from backend.drivers.base import StorageDriver


class JSONStorageDriver(StorageDriver):
    def __init__(self, cfg_obj):
        self.cfg = cfg_obj
        self.cfg = cfg

    def get_section(self, section: str) -> Any:
        return self._cfg.get_section(section)

    def get_properties(self, pool: str, dataset: str) -> Dict[str, Any]:
        return {}

    def set_property(self, pool: str, dataset: str, prop: str, value: str) -> Dict[str, Any]:
        return {"error":"not_implemented"}


    def set_section(self, section: str, value: Any) -> None:
        self._cfg.set_section(section, value)

     # backend/drivers/json_driver.py

    def list_disks(self) -> List[Dict[str, Any]]:
        return self.cfg.get_section("disks") or []

    def list_pools(self) -> List[Dict[str, Any]]:
        return self.cfg.get_storage().get("pools", [])

    def create_pool(self, name: str, layout: Dict[str, Any], dry_run: bool=False) -> Dict[str, Any]:
        preview = {"name": name, "layout": layout}
        if dry_run:
            return {"dry_run": True, "preview": preview}
        storage = self.cfg.get_storage()
        pools = storage.get("pools", [])
        pools.append(preview)
        self.cfg.update_storage({"pools": pools, "datasets": storage.get("datasets", [])})
        return {"created": True, "pool": preview}

    def destroy_pool(self, name: str, force: bool=False) -> Dict[str, Any]:
        storage = self.cfg.get_storage()
        pools = [p for p in storage.get("pools", []) if p.get("name") != name]
        self.cfg.update_storage({"pools": pools, "datasets": storage.get("datasets", [])})
        return {"deleted": True}

    def list_datasets(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        ds = self.cfg.get_storage().get("datasets", [])
        if pool: return [d for d in ds if d.get("pool")==pool]
        return ds

    def create_dataset(self, pool: str, name: str, mountpoint: Optional[str]=None) -> Dict[str, Any]:
        ds = {"pool": pool, "name": name, "mountpoint": mountpoint}
        storage = self.cfg.get_storage()
        datasets = storage.get("datasets", [])
        datasets.append(ds)
        self.cfg.update_storage({"pools": storage.get("pools", []), "datasets": datasets})
        return {"created": True, "dataset": ds}

    def destroy_dataset(self, pool: str, name: str, recursive: bool=False) -> Dict[str, Any]:
        storage = self.cfg.get_storage()
        datasets = [d for d in storage.get("datasets", []) if not (d["pool"]==pool and d["name"]==name)]
        self.cfg.update_storage({"pools": storage.get("pools", []), "datasets": datasets})
        return {"deleted": True}

    def list_snapshots(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        return []

    def create_snapshot(self, dataset: str, snapshot_name: str) -> Dict[str, Any]:
        return {"error": "not_supported"}

    def destroy_snapshot(self, snapshot: str) -> Dict[str, Any]:
        return {"error": "not_supported"}

    def list_shares(self) -> List[Dict[str, Any]]:
        return self.cfg.list_shares()

    def create_share(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        self.cfg.add_share(meta)
        return {"created": True}

    def delete_share(self, name: str) -> Dict[str, Any]:
        self.cfg.remove_share(name)
        return {"deleted": True}

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
        self.cfg.remove_acl(path, username)
        return {"removed": True}

    def smart_health(self, devpath: str) -> Dict[str, Any]:
        return {"error": "not_supported"}

    def ping(self) -> Dict[str, Any]:
        return {"ok": True, "driver": "json"}


    