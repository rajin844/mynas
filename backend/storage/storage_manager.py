from backend.drivers.driver_loader import get_driver
from backend.managers.zfs_manager import zfs_manager
from typing import Dict, Any, List
import json, subprocess, logging
#from backend.app.driver_persistence import driverdb
logger = logging.getLogger("mynas.storage_manager")

driver = get_driver()


class StorageManager:
    def __init__(self):
        self.driver = get_driver()

    # ---------------------------------------------------------
    # DISKS
    # ---------------------------------------------------------
    def list_disks(self) -> List[Dict[str, Any]]:
        return self.driver.list_disks()
    
    def get_storage_summary() -> Dict[str, Any]:
     pools = self.driver.list_pools()
     datasets = self.driver.list_datasets()
     disks = self.driver.list_disks()
     return {
        "disks": disks,
        "pools": pools,
        "datasets": datasets,
        "counts": {"disks": len(disks), "pools": len(pools), "datasets": len(datasets)},
     }
    
    def summary2(self) -> Dict[str, Any]:
        return {
            "disks": self.driver.list_disks(),
            "pools": zfs_manager.list_pools(),
            "datasets": zfs_manager.list_datasets(None),
        }

    # ---------------------------------------------------------
    # SMART / HEALTH
    # ---------------------------------------------------------
    def smart_health(self, devpath: str):
      return self.driver.smart_health(devpath)
# Global instance
storage_manager = StorageManager()

