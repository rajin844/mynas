from fastapi import HTTPException
import os
import subprocess
from fastapi import HTTPException
from typing import List, Dict, Optional
from backend.app.config_manager import ConfigManager
from backend.app.utils.zfs_ops import (
    create_dataset,
    delete_dataset,
    list_datasets,
    zpool_list,
    zpool_import_list
)
from backend.realtime.events import emit_event

cfg = ConfigManager()

"""
ZFS Dataset Manager
Handles create, delete, modify, and list operations for datasets.
"""



# ------------------------------
# List Datasets
# ------------------------------
def list_datasets_api(pool: str = None) -> List[Dict]:
    """
    Return all ZFS datasets visible on the system and any stored metadata.
    """
    system_datasets = list_datasets()
    stored = cfg.get_section("storage") or {}
    user_datasets = stored.get("datasets", [])
    # Merge system + config metadata (keep unique)
    existing_names = {d["name"] for d in system_datasets}
    for ds in user_datasets:
        if ds["name"] not in existing_names:
            system_datasets.append(ds)
    return system_datasets




# ------------------------------
# Create Dataset
# ------------------------------
def create_dataset_api(pool: str, name: str, mountpoint: str = "") -> Dict[str, bool]:
    """
    Create a new dataset under a given pool and record in config.json.
    """
    if not pool or not name:
        raise HTTPException(status_code=400, detail="Pool and dataset name required")

    ok = create_dataset(pool, name)
    if ok:
        storage = cfg.get_section("storage") or {}
        datasets = storage.get("datasets", [])
        ds_path = f"{pool}/{name}"
        entry = {"name": ds_path, "pool": pool, "mountpoint": mountpoint}
        datasets.append(entry)
        storage["datasets"] = datasets
        cfg.set_section("storage", storage)
        emit_event({
            "module": "storage",
            "action": "dataset_created",
            "dataset": ds_path
        })
    return {"ok": ok}


# ------------------------------
# Delete Dataset
# ------------------------------
def delete_dataset_api(pool: str, name: str) -> Dict[str, bool]:
    """
    Destroy a dataset and remove from config.json.
    """
    if not pool or not name:
        raise HTTPException(status_code=400, detail="Pool and dataset name required")

    ok = delete_dataset(pool, name)
    if ok:
        storage = cfg.get_section("storage") or {}
        datasets = [d for d in storage.get("datasets", [])
                    if d.get("name") != f"{pool}/{name}"]
        storage["datasets"] = datasets
        cfg.set_section("storage", storage)
        emit_event({
            "module": "storage",
            "action": "dataset_deleted",
            "dataset": f"{pool}/{name}"
        })
    return {"ok": ok}


# ------------------------------
# Modify Dataset
# ------------------------------
def modify_dataset_api(
    pool: str,
    name: str,
    new_name: Optional[str] = None,
    new_mountpoint: Optional[str] = None,
) -> Dict[str, bool]:
    """
    Modify a dataset's name or mountpoint.
    In real systems, use `zfs rename` or `zfs set mountpoint=/path`.
    Here we mock those operations for safe development.
    """
    if not pool or not name:
        raise HTTPException(status_code=400, detail="Pool and dataset name required")

    ds_full = f"{pool}/{name}"
    storage = cfg.get_section("storage") or {}
    datasets = storage.get("datasets", [])
    ds_entry = next((d for d in datasets if d.get("name") == ds_full), None)
    if not ds_entry:
        raise HTTPException(status_code=404, detail=f"Dataset {ds_full} not found")

    ok = True
    try:
        # Rename dataset (mock)
        if new_name:
            new_full = f"{pool}/{new_name}"
            ds_entry["name"] = new_full
            # real: subprocess.run(["zfs", "rename", ds_full, new_full], check=True)
        # Change mountpoint
        if new_mountpoint:
            ds_entry["mountpoint"] = new_mountpoint
            # real: subprocess.run(["zfs", "set", f"mountpoint={new_mountpoint}", ds_entry["name"]], check=True)

        cfg.set_section("storage", storage)
        emit_event({
            "module": "storage",
            "action": "dataset_modified",
            "dataset": ds_entry["name"],
            "changes": {
                "old": ds_full,
                "new_name": new_name,
                "new_mountpoint": new_mountpoint
            }
        })
    except Exception as e:
        print(f"[ERROR] modify_dataset_api failed: {e}")
        ok = False
    return {"ok": ok}
    
def list_zfs_datasets(pool: str = None):
    """
    If pool provided → list datasets under that pool
    Else → list all datasets
    """
    datasets = []

    if pool:
        cmd = ["zfs", "list", "-H", "-o", "name", "-r", pool]
    else:
        cmd = ["zfs", "list", "-H", "-o", "name"]

    try:
        out = subprocess.check_output(cmd).decode().strip().split("\n")
        for line in out:
            if line:
                datasets.append(line)
        return datasets

    except Exception:
        return []