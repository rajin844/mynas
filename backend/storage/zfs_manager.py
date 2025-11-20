# backend/managers/zfs_manager.py
"""
ZFSManager (Driver-Only)
All ZFS operations are delegated to StorageDriver(ZfsDriver or others)
No direct subprocess here. Manager = High-level API for REST/RPC.
"""

from typing import List, Dict, Any, Optional
from backend.drivers.driver_loader import get_driver
from backend.app.task_queue import enqueue_task, start_background_worker

class ZFSManager:
    def __init__(self):
        self.driver = get_driver()
        start_background_worker()  # ensure worker started

    # ---------------------------------------------------------
    # POOLS
    # ---------------------------------------------------------
    def list_pools(self) -> List[Dict[str, Any]]:
        return self.driver.list_pools()

    def create_pool(self, name: str, layout: dict, dry_run=False, run_async=False) -> Dict[str, Any]:
        """
        If run_async True -> enqueue background job and return task_id.
        """
        if dry_run:
            return self.driver.create_pool(name, layout, dry_run=True)

        if run_async:
            task_id = enqueue_task("create_pool", {"name": name, "layout": layout})
            return {"enqueued": True, "task_id": task_id}
        # direct blocking create
        return self.driver.create_pool(name, layout, dry_run=False)

    def destroy_pool(self, name: str, force=False) -> Dict[str, Any]:
        return self.driver.destroy_pool(name, force=force)

    # ---------------------------------------------------------
    # DATASETS
    # ---------------------------------------------------------
    def list_datasets(self, pool: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.driver.list_datasets(pool)

    def create_dataset(self, pool: str, name: str, mountpoint: Optional[str] = None) -> Dict[str, Any]:
        return self.driver.create_dataset(pool, name, mountpoint)

    def destroy_dataset(self, pool: str, name: str, recursive=False) -> Dict[str, Any]:
        return self.driver.destroy_dataset(pool, name, recursive)

    # ---------------------------------------------------------
    # SNAPSHOTS
    # ---------------------------------------------------------
    def list_snapshots(self, pool: Optional[str] = None):
        return self.driver.list_snapshots(pool)

    def create_snapshot(self, dataset: str, snap_name: str):
        return self.driver.create_snapshot(dataset, snap_name)

    def destroy_snapshot(self, snapshot: str):
        return self.driver.destroy_snapshot(snapshot)

    # ---------------------------------------------------------
    # SMART / HEALTH
    # ---------------------------------------------------------
    def smart_health(self, devpath: str):
        return self.driver.smart_health(devpath)

# Global instance
zfs_manager = ZFSManager()
