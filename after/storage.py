#from fastapi import HTTPException
#from typing import List, Dict, Optional
#from app.config_manager import ConfigManager
#from app.utils.zfs_ops import (
#    PoolInfo,
 #   DatasetInfo,
  #  zpool_list,
   # zpool_import_list,
    #create_pool,
   # destroy_pool,
    #import_pool,
    #create_dataset,
    #delete_dataset,
   # list_datasets,
  #
  #from app.realtime.events import emit_event

  #cfg = ConfigManager()

"""
ZFS Manager
Manages both Pools and Datasets:
- Create / Import / Destroy / List Pools
- Create / Modify / Delete / List Datasets
"""

# ====================================================
# POOL MANAGEMENT
# ====================================================

def list_pools_api() -> Dict[str, List[PoolInfo]]:
    """
    Return all pools:
    - from config.json
    - from zpool list
    - from zpool import (importable)
    """
    stored = cfg.get_section("storage") or {}
    config_pools = stored.get("pools", [])
    return {
        "config_pools": config_pools,
        "zpool_list": zpool_list(),
        "importable_pools": zpool_import_list(),
    }


def create_pool_api(name: str, devices: List[str]) -> Dict[str, bool]:
    """
    Create a new ZFS pool and record in config.json.
    """
    if not name or not devices:
        raise HTTPException(status_code=400, detail="Pool name and devices required")

    ok = create_pool(name, devices)
    if ok:
        storage = cfg.get_section("storage") or {}
        pools = storage.get("pools", [])
        pool_entry = {"name": name, "devices": devices}
        pools.append(pool_entry)
        storage["pools"] = pools
        cfg.set_section("storage", storage)
        emit_event({
            "module": "storage",
            "action": "pool_created",
            "name": name,
            "devices": devices
        })
    return {"ok": ok}


def import_pool_api(name: str) -> Dict[str, bool]:
    """
    Import existing ZFS pool (visible via zpool import).
    """
    if not name:
        raise HTTPException(status_code=400, detail="Pool name required")

    ok = import_pool(name)
    if ok:
        storage = cfg.get_section("storage") or {}
        pools = storage.get("pools", [])
        if not any(p["name"] == name for p in pools):
            pools.append({"name": name, "devices": []})
        storage["pools"] = pools
        cfg.set_section("storage", storage)
        emit_event({
            "module": "storage",
            "action": "pool_imported",
            "name": name
        })
    return {"ok": ok}


def destroy_pool_api(name: str) -> Dict[str, bool]:
    """
    Destroy existing pool and remove from config.json.
    """
    if not name:
        raise HTTPException(status_code=400, detail="Pool name required")

    ok = destroy_pool(name)
    if ok:
        storage = cfg.get_section("storage") or {}
        pools = [p for p in storage.get("pools", []) if p.get("name") != name]
        storage["pools"] = pools
        cfg.set_section("storage", storage)
        emit_event({
            "module": "storage",
            "action": "pool_deleted",
            "name": name
        })
    return {"ok": ok}

# ====================================================
# DATASET MANAGEMENT
# ====================================================

def list_datasets_api() -> List[DatasetInfo]:
    """
    Return all datasets (from system + config.json).
    """
    system_datasets = list_datasets()
    stored = cfg.get_section("storage") or {}
    user_datasets = stored.get("datasets", [])
    existing_names = {d["name"] for d in system_datasets}
    for ds in user_datasets:
        if ds["name"] not in existing_names:
            system_datasets.append(ds)
    return system_datasets


def create_dataset_api(pool: str, name: str, mountpoint: str = "") -> Dict[str, bool]:
    """
    Create a new dataset and record in config.json.
    """
    if not pool or not name:
        raise HTTPException(status_code=400, detail="Pool and dataset name required")

    ok = create_dataset(pool, name)
    if ok:
        storage = cfg.get_section("storage") or {}
        datasets = storage.get("datasets", [])
        ds_full = f"{pool}/{name}"
        entry = {"name": ds_full, "pool": pool, "mountpoint": mountpoint}
        datasets.append(entry)
        storage["datasets"] = datasets
        cfg.set_section("storage", storage)
        emit_event({
            "module": "storage",
            "action": "dataset_created",
            "dataset": ds_full
        })
    return {"ok": ok}


def delete_dataset_api(pool: str, name: str) -> Dict[str, bool]:
    """
    Delete dataset and remove from config.json.
    """
    if not pool or not name:
        raise HTTPException(status_code=400, detail="Pool and dataset name required")

    ok = delete_dataset(pool, name)
    if ok:
        storage = cfg.get_section("storage") or {}
        datasets = [d for d in storage.get("datasets", []) if d.get("name") != f"{pool}/{name}"]
        storage["datasets"] = datasets
        cfg.set_section("storage", storage)
        emit_event({
            "module": "storage",
            "action": "dataset_deleted",
            "dataset": f"{pool}/{name}"
        })
    return {"ok": ok}


def modify_dataset_api(
    pool: str,
    name: str,
    new_name: Optional[str] = None,
    new_mountpoint: Optional[str] = None,
) -> Dict[str, bool]:
    """
    Modify dataset (rename or change mountpoint).
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
        if new_name:
            ds_entry["name"] = f"{pool}/{new_name}"
        if new_mountpoint:
            ds_entry["mountpoint"] = new_mountpoint

        storage["datasets"] = datasets
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
