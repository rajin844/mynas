# backend/managers/share_manager.py
"""
ShareManager (Driver-Only)
SMB/NFS shares stored in DB (via driver)
"""

from typing import List, Dict, Any
from backend.drivers.driver_loader import get_driver

class ShareManager:
    def __init__(self):
        self.driver = get_driver()

    def list_shares(self) -> List[Dict[str, Any]]:
        return self.driver.list_shares()

    def create_share(self, meta: Dict[str, Any]):
        return self.driver.create_share(meta)

    def delete_share(self, name: str):
        return self.driver.delete_share(name)

share_manager = ShareManager()
