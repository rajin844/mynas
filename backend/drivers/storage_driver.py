# backend/drivers/storage_driver.py
"""
Storage driver interface and factory.

Provides a single entrypoint: get_storage_driver()
Default driver: MySQLStorageDriver (backend.drivers.storage_driver_mysql)
You can swap to another driver by setting STORAGE_DRIVER env var to the full module path.
"""

from typing import Protocol, Any, Dict, List, Optional
import os
import importlib
import logging

logger = logging.getLogger("mynas.storage_driver")


class StorageDriverProtocol(Protocol):
    """
    Minimal interface used by storage_manager / zfs_manager / smart_manager.
    Implement async methods below in each driver.
    """

    async def list_disks_db(self) -> List[Dict[str, Any]]:
        """Return list of disks from DB (if stored)."""

    async def save_disk_record(self, disk: Dict[str, Any]) -> Any:
        """Insert/Update disk record"""

    async def list_pools_db(self) -> List[Dict[str, Any]]:
        """Return pools from DB"""

    async def create_pool_record(self, pool: Dict[str, Any]) -> Any:
        """Insert pool record"""

    async def remove_pool_record(self, pool_name: str) -> Any:
        """Remove pool record"""

    async def list_datasets_db(self, pool: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return datasets (optionally for pool)"""

    async def create_dataset_record(self, pool: str, name: str, mountpoint: Optional[str] = None) -> Any:
        """Create dataset DB record"""

    async def delete_dataset_record(self, pool: str, name: str) -> Any:
        """Delete dataset DB record"""

    async def add_smart_history(self, disk_name: str, raw: Dict[str, Any], status: str, temp_c: Optional[float]) -> Any:
        """Add a SMART history row"""

    async def push_alert(self, level: str, source: str, message: str) -> Any:
        """Push an alert to alerts table"""

    # any other helpers as needed


_default_driver = "backend.drivers.storage_driver_mysql"


def _import_driver(module_path: str):
    module = importlib.import_module(module_path)
    # Expect module to export `MySQLStorageDriver` or `StorageDriver`
    if hasattr(module, "StorageDriver"):
        return module.StorageDriver
    if hasattr(module, "MySQLStorageDriver"):
        return module.MySQLStorageDriver
    raise ImportError(f"No StorageDriver class found in {module_path}")


def get_storage_driver() -> StorageDriverProtocol:
    """
    Instantiate storage driver according to ENV var or default.
    This returns a singleton instance (module-level).
    """
    global _driver_instance
    try:
        _driver_instance  # type: ignore
    except NameError:
        _driver_instance = None  # type: ignore

    if _driver_instance is not None:
        return _driver_instance  # type: ignore

    module_path = os.environ.get("STORAGE_DRIVER", _default_driver)
    try:
        DriverClass = _import_driver(module_path)
        _driver_instance = DriverClass()  # type: ignore
        logger.info(f"Storage driver loaded: {module_path}")
        return _driver_instance  # type: ignore
    except Exception as e:
        logger.exception("Failed to load storage driver %s: %s", module_path, e)
        # fallback to default
        DriverClass = _import_driver(_default_driver)
        _driver_instance = DriverClass()  # type: ignore
        return _driver_instance  # type: ignore
