# backend/app/storage_driver.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class StorageDriver(ABC):
    """
    Abstract storage driver used by managers.
    Implementations must be threadsafe (or manager must serialize access).
    """
    
     # Disks / Inventory
    @abstractmethod
    def list_disks(self) -> List[Dict[str, Any]]: ...

    
   # Pools
    @abstractmethod
    def list_pools(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def create_pool(self, name: str, layout: Dict[str, Any], dry_run: bool=False) -> Dict[str, Any]: ...
    @abstractmethod
    def destroy_pool(self, name: str, force: bool=False) -> Dict[str, Any]: ...


  # Datasets
    @abstractmethod
    def list_datasets(self, pool: Optional[str]=None) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def create_dataset(self, pool: str, name: str, mountpoint: Optional[str]=None) -> Dict[str, Any]: ...
    @abstractmethod
    def destroy_dataset(self, pool: str, name: str, recursive: bool=False) -> Dict[str, Any]: ...


    # --- shares ---
    @abstractmethod
    def list_shares(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def create_share(self, meta: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def delete_share(self, name: str) -> Dict[str, Any]: ...

    # --- users ---
    @abstractmethod
    def list_users(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def save_user(self, user: Dict[str, Any]) -> None: ...
    @abstractmethod
    def remove_user(self, username: str) -> None: ...

     # ACLs / Permissions
    @abstractmethod
    def list_acls(self, path: str) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def set_acl(self, path: str, acl: List[Dict[str, Any]]) -> Dict[str, Any]: ...
    @abstractmethod
    def remove_acl(self, path: str, username: str) -> Dict[str, Any]: ...

    # --- generic get/set for other sections ---
    @abstractmethod
    def get_section(self, section: str) -> Any: ...
    @abstractmethod
    def set_section(self, section: str, value: Any) -> None: ...


     # -------- MOUNTING ----------------------------------------------
    @abstractmethod
    def mount_dataset(self, pool: str, name: str, mountpoint: str) -> Dict[str, Any]: ...
    @abstractmethod
    def unmount_dataset(self, pool: str, name: str) -> Dict[str, Any]: ...

    # -------- PROPERTIES --------------------------------------------
    @abstractmethod
    def get_properties(self, pool: str, dataset: str) -> Dict[str, Any]: ...
    @abstractmethod
    def set_property(self, pool: str, dataset: str, prop: str, value: str) -> Dict[str, Any]: ...

      # Snapshots
    @abstractmethod
    def list_snapshots(self, pool: Optional[str]=None) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def create_snapshot(self, dataset: str, snapshot_name: str) -> Dict[str, Any]: ...
    @abstractmethod
    def destroy_snapshot(self, snapshot: str) -> Dict[str, Any]: ...

    # ───── DISKS ─────────────────────────────
    @abstractmethod
    def list_disks(self) -> List[Dict]: ...

    # -------- BACKEND TYPE ------------------------------------------
    @abstractmethod
    def backend_type(self) -> str: ...

    # SMART
    @abstractmethod
    def smart_health(self, devpath: str) -> Dict[str, Any]: ...

    # Utilities
    @abstractmethod
    def ping(self) -> Dict[str, Any]: ...