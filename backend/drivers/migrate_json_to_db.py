# backend/migrate_json_to_db.py
from backend.app.config_manager import cfg
from backend.drivers.sqlite_driver import SQLiteDriver
import os, json

def migrate_to_sqlite(sqlite_path=None):
    drv = SQLiteDriver(cfg)
    storage = cfg.get_storage()
    pools = storage.get("pools", [])
    datasets = storage.get("datasets", [])
    for p in pools:
        name = p.get("name")
        layout = p.get("layout") or {"type": p.get("type","zfs"), "devices": p.get("devices", [])}
        print("Migrating pool:", name)
        drv.create_pool(name, layout, dry_run=False)
    for d in datasets:
        print("Migrating dataset:", d.get("name"))
        drv.create_dataset(d["pool"], d["name"], d.get("mountpoint"))
    for s in cfg.list_shares():
        drv.create_share(s)
    for u in cfg.list_users():
        if hasattr(drv, "create_user"):
            try:
                drv.create_user(u)
            except:
                pass
    for a in cfg.list_acls():
        try:
            drv.set_acl(a["path"], [{"username": a["user"], "permissions": a["permissions"]}])
        except:
            pass
    print("Migration JSON->SQLite complete")

def migrate_to_mysql(cfg_mysql):
    # Use sqlite path driver as helper or implement MySQLDriver interface similarly
    from backend.drivers.mysql_driver import MySQLDriver
    drv = MySQLDriver(cfg)
    storage = cfg.get_storage()
    pools = storage.get("pools", [])
    datasets = storage.get("datasets", [])
    for p in pools:
        drv.create_pool(p.get("name"), p.get("layout") or {"type": p.get("type","zfs"), "devices": p.get("devices", [])}, dry_run=False)
    for d in datasets:
        drv.create_dataset(d["pool"], d["name"], d.get("mountpoint"))
    for s in cfg.list_shares():
        drv.create_share(s)
    print("Migration JSON->MySQL complete")

if __name__ == "__main__":
    migrate_to_sqlite()
