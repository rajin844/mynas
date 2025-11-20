from fastapi import APIRouter, Body, HTTPException
from backend.app.driver_loader import driver
from backend.storage.storage_manager import list_disks, get_storage_summary, create_pool, list_pools 

@router.post("/listdisks")
def api_list_disks():
    # heavy command - run lsblk
    return {"response": list_disks(), "error": None}
    
@router.post("/summary")
def api_storage_summary():
    try:
        return {"response": get_storage_summary(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/listpools")
def api_list_pools():
    return {"response": list_pools(), "error": None}    

@router.post("/createpool")
def api_zcreate_pool(payload: Dict[str, Any] = Body(...)):
    """
    payload:
    {
      name: str,
      devices: ["/dev/sdb",...],
      pool_type: "zfs"/"ext4"/"btrfs"/"cloud",
      raidz: "raidz1"/"raidz2"/"mirror"/"single",
      dry_run: true|false
    }
    """
    name = payload.get("name")
    devices = payload.get("devices", [])
    pool_type = payload.get("pool_type", "zfs")
    raidz = payload.get("raidz")
    dry_run = payload.get("dry_run", True)

    if not name or not devices:
        raise HTTPException(status_code=400, detail="name and devices required")

    # dispatch to proper driver
    if pool_type == "zfs":
        from backend.app.drivers.zfs_driver import ZFSStorageDriver
        drv = ZFSStorageDriver()
    elif pool_type == "ext4":
        from backend.app.drivers.ext4_driver import EXT4StorageDriver
        drv = EXT4StorageDriver()
    elif pool_type == "btrfs":
        from backend.app.drivers.btrfs_driver import BTRFSStorageDriver
        drv = BTRFSStorageDriver()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported pool_type {pool_type}")

    res = drv.create_pool(name, devices, raidz=raidz, dry_run=dry_run)
    return {"response": res, "error": None}

    
@router.post("/createpool")
def api_create_pool(payload: dict = Body(...)):
    name = payload.get("name")
    layout = payload.get("layout") or {"type": payload.get("raidz"), "devices": payload.get("devices")}
    dry_run = payload.get("dry_run", True)
    if not name or not layout:
        raise HTTPException(status_code=400, detail="name and layout required")
    res = create_pool(name, layout, dry_run=dry_run)
    return {"response": res, "error": None}
