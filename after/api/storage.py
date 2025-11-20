from fastapi import APIRouter, HTTPException
from typing import List, Dict
from backend.storage.storage_manager import (
    detect_disks,
    disk_info,
    list_filesystems,
    mount_disk,
    list_pools,
    create_pool_api,
    destroy_pool_api,
    import_pool_api,
)
from backend.storage.zfs_manager import (
    list_datasets_api,
    create_dataset_api,
    delete_dataset_api,
    modify_dataset_api,
)

router = APIRouter(prefix="/storage", tags=["Storage"])

# ----------------------------------
# 🧠 Disk Management
# ----------------------------------

@router.get("/disks", summary="List all detected disks")
def api_list_disks() -> Dict[str, List[str]]:
    """Detect all available block devices"""
    disks = detect_disks()
    return {"disks": disks}


@router.get("/disks/info", summary="Get detailed info for a disk")
def api_disk_info(name: str):
    """Get disk partitions and mount points"""
    if not name:
        raise HTTPException(status_code=400, detail="Disk name required")
    return disk_info(f"/dev/{name}")


@router.get("/filesystems", summary="List filesystem types per device")
def api_list_filesystems():
    """List all known filesystems"""
    return list_filesystems()


@router.post("/mount", summary="Mount a disk to a path")
def api_mount_disk(disk: str, path: str):
    ok = mount_disk(disk, path)
    if not ok:
        raise HTTPException(status_code=500, detail=f"Failed to mount {disk}")
    return {"ok": ok}


# ----------------------------------
# 🧩 Pool Management (ZFS)
# ----------------------------------

@router.get("/pools", summary="List ZFS pools (configured, active, importable)")
def api_list_pools():
    """Return config pools, live ZFS pools, and importable pools"""
    return list_pools()


@router.post("/pools/create", summary="Create a new ZFS pool")
def api_create_pool(payload: dict):
    """Create a new ZFS pool from provided devices"""
    name = payload.get("name")
    devices = payload.get("devices", [])
    if not name or not devices:
        raise HTTPException(status_code=400, detail="Pool name and devices required")
    return create_pool_api(name, devices)


@router.post("/pools/import", summary="Import an existing ZFS pool")
def api_import_pool(payload: dict):
    """Import existing pool by name"""
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Pool name required")
    return import_pool_api(name)


@router.delete("/pools/delete", summary="Destroy a ZFS pool")
def api_destroy_pool(payload: dict):
    """Destroy an existing ZFS pool"""
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Pool name required")
    return destroy_pool_api(name)


# ----------------------------------
# 📦 Dataset Management
# ----------------------------------

@router.get("/datasets", summary="List all datasets")
def api_list_datasets():
    """List datasets from ZFS and config.json"""
    return list_datasets_api()


@router.post("/datasets/create", summary="Create a new dataset")
def api_create_dataset(payload: dict):
    pool = payload.get("pool")
    name = payload.get("name")
    mountpoint = payload.get("mountpoint", "")
    if not pool or not name:
        raise HTTPException(status_code=400, detail="Pool and dataset name required")
    return create_dataset_api(pool, name, mountpoint)


@router.delete("/datasets/delete", summary="Delete dataset")
def api_delete_dataset(payload: dict):
    pool = payload.get("pool")
    name = payload.get("name")
    if not pool or not name:
        raise HTTPException(status_code=400, detail="Pool and dataset name required")
    return delete_dataset_api(pool, name)


@router.put("/datasets/modify", summary="Modify dataset properties")
def api_modify_dataset(payload: dict):
    pool = payload.get("pool")
    name = payload.get("name")
    new_name = payload.get("new_name")
    new_mountpoint = payload.get("new_mountpoint")
    if not pool or not name:
        raise HTTPException(status_code=400, detail="Pool and dataset name required")
    return modify_dataset_api(pool, name, new_name, new_mountpoint)
