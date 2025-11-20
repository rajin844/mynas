# backend/app/driver_persistence.py
from backend.app.config_manager import cfg
from typing import List, Dict, Any, Optional

class driverdb:
    @staticmethod
    def list_pools(type: Optional[str] = None) -> List[Dict[str, Any]]:
        storage = cfg.get_storage()
        pools = storage.get("pools", [])
        if type:
            return [p for p in pools if p.get("type") == type]
        return pools

    @staticmethod
    def get_pool(name: str) -> Optional[Dict[str, Any]]:
        pools = driverdb.list_pools()
        for p in pools:
            if p.get("name") == name:
                return p
        return None

    @staticmethod
    def save_pool(pool: Dict[str, Any]) -> None:
        storage = cfg.get_storage()
        pools = storage.setdefault("pools", [])
        pools = [p for p in pools if p.get("name") != pool.get("name")]
        pools.append(pool)
        cfg.update_storage(storage)

    @staticmethod
    def remove_pool(name: str) -> None:
        storage = cfg.get_storage()
        storage["pools"] = [p for p in storage.get("pools", []) if p.get("name") != name]
        cfg.update_storage(storage)

    # datasets
    @staticmethod
    def list_datasets(pool: Optional[str] = None) -> List[Dict[str, Any]]:
        arr = cfg.get_storage().get("datasets", [])
        if pool:
            return [d for d in arr if d.get("pool") == pool]
        return arr

    @staticmethod
    def save_dataset(ds: Dict[str, Any]) -> None:
        storage = cfg.get_storage()
        datasets = storage.setdefault("datasets", [])
        datasets = [d for d in datasets if not (d.get("pool")==ds.get("pool") and d.get("name")==ds.get("name"))]
        datasets.append(ds)
        cfg.update_storage(storage)

    @staticmethod
    def remove_dataset(pool: str, name: str) -> None:
        storage = cfg.get_storage()
        storage["datasets"] = [d for d in storage.get("datasets", []) if not (d.get("pool")==pool and d.get("name")==name)]
        cfg.update_storage(storage)

    # users, shares, acls - delegate to cfg where possible
    @staticmethod
    def list_users() -> List[Dict[str, Any]]:
        return cfg.list_users()

    @staticmethod
    def save_user(user: Dict[str, Any]) -> None:
        cfg.add_user(user)

    @staticmethod
    def list_shares() -> List[Dict[str, Any]]:
        return cfg.list_shares()

    @staticmethod
    def list_acls() -> List[Dict[str, Any]]:
        return cfg.list_acls()
