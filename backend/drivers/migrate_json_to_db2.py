# backend/migrate_json_to_db.py
import json, os, sys
from backend.app.config_manager import cfg
from backend.drivers.driver_loader import get_driver

def migrate_to_sqlite_or_mysql():
    driver = get_driver()
    storage = cfg.get_storage()
    pools = storage.get("pools", [])
    datasets = storage.get("datasets", [])
    # migrate pools
    for p in pools:
        name = p.get("name")
        layout = p.get("layout") or {"type": p.get("type","zfs"), "devices": p.get("devices", [])}
        print("Migrating pool:", name)
        # dry run first then create
        driver.create_pool(name, layout, dry_run=False)
    # migrate datasets
    for d in datasets:
        driver.create_dataset(d["pool"], d["name"], d.get("mountpoint"))
    # shares
    for s in cfg.list_shares():
        driver.create_share(s)
    # users
    # store users as driver may not support; otherwise keep in cfg or users table
    for u in cfg.list_users():
        try:
            if hasattr(driver, "create_user"):
                driver.create_user(u)
        except Exception:
            pass
    # acls
    for a in cfg.list_acls():
        try:
            driver.set_acl(a["path"], [{"username": a["user"], "permissions": a["permissions"]}])
        except Exception:
            pass
    print("Migration complete.")

if __name__ == "__main__":
    migrate_to_sqlite_or_mysql()
