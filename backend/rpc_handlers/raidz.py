# backend/rpc_handlers/raidz.py
from backend.storage.raidz_manager import build_layout
from backend.storage.zfs_manager import create_pool

def rpc_preview(disks: list, layout: str = "single"):
    return build_layout(disks, layout)

def rpc_create(disks: list, layout: str = "single", pool_name: str = None, dry_run: bool = True):
    preview = build_layout(disks, layout)
    if dry_run:
        # offer preview + proposed cmd
        devices = [d for v in preview.get("vdevs", []) for d in v]
        cmd_preview = create_pool(pool_name or "preview", devices, raidz=(layout if layout!="single" else "single"), dry_run=True)
        return {"preview": preview, "cmd_preview": cmd_preview}
    devices = [d for v in preview.get("vdevs", []) for d in v]
    return create_pool(pool_name or "pool", devices, raidz=(layout if layout!="single" else "single"), dry_run=dry_run)

def register_rpc(register):
    register("raidz", {
        "preview": rpc_preview,
        "create": rpc_create,
    })
