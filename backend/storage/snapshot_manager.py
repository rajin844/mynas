# backend/storage/snapshot_manager.py
"""
Snapshot manager: list/create/destroy/rollback/clone snapshots
Uses zfs snapshots when available; otherwise uses config store.
"""
import shutil
import subprocess
import logging
import time
from typing import List, Dict, Any

# backend/storage/snapshot_manager.py
from backend.drivers.driver_loader import get_driver

class SnapshotManager:
    def __init__(self):
        self.driver = get_driver()

    def list(self, pool: Optional[str] = None):
        return self.driver.list_snapshots(pool)

    def create(self, dataset: str, name: str):
        return self.driver.create_snapshot(dataset, name)

    def destroy(self, snapshot: str):
        return self.driver.destroy_snapshot(snapshot)

snapshot_manager = SnapshotManager()