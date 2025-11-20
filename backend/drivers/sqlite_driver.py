# backend/drivers/sqlite_driver.py
import sqlite3, json, os
from typing import List, Dict, Any, Optional
from backend.drivers.base import StorageDriver

DB_PATH = os.environ.get("MYNAS_DB", "/var/lib/mynas/mynas.db")

class SQLiteDriver(StorageDriver):
    def __init__(self, cfg):
        self.cfg = cfg
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pools (name TEXT PRIMARY KEY, type TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS datasets (id INTEGER PRIMARY KEY, pool TEXT, name TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS shares (name TEXT PRIMARY KEY, data TEXT);
        CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, data TEXT);
        CREATE TABLE IF NOT EXISTS acls (id INTEGER PRIMARY KEY, path TEXT, username TEXT, data TEXT);
        """)
        self.conn.commit()

    def _row_to_json(self, row):
        if row is None: return None
        d = dict(row)
        if d.get("data"):
            try:
                d.update(json.loads(d["data"]))
            except:
                pass
        return d

    # list_disks uses lsblk
    def list_disks(self) -> List[Dict[str, Any]]:
        import subprocess, json as _json
        try:
            out = subprocess.check_output(["lsblk","-J","-o","NAME,KNAME,SIZE,MODEL,ROTA,MOUNTPOINT"]).decode()
            j = _json.loads(out)
            disks = []
            for d in j.get("blockdevices", []):
                if d.get("type") == "disk":
                    disks.append({
                        "name": d.get("name"),
                        "devpath": "/dev/" + d.get("kname"),
                        "size": d.get("size"),
                        "model": d.get("model"),
                        "rotational": bool(d.get("rota")),
                        "mountpoint": d.get("mountpoint")
                    })
            return disks
        except Exception:
            return []

    def list_pools(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT name, type, data FROM pools")
        rows = cur.fetchall()
        out = []
        for r in rows:
            d = {"name": r["name"], "type": r["type"]}
            if r["data"]:
                try:
                    d.update(json.loads(r["data"]))
                except:
                    pass
            out.append(d)
        return out

    def create_pool(self, name: str, layout: Dict[str, Any], dry_run: bool=False) -> Dict[str, Any]:
        # layout: {"type":"raidz1", "devices":["/dev/sdb","/dev/sdc"]}
        if dry_run:
            return {"dry_run": True, "cmd_preview": self._build_zpool_cmd(name, layout)}
        # run actual zpool create if zfs
        if layout.get("type","").startswith("raidz") or layout.get("type") in ["mirror","single"]:
            import subprocess
            cmd = self._build_zpool_cmd(name, layout)
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                return {"created": False, "error": p.stderr}
        # persist metadata
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO pools (name,type,data) VALUES (?,?,?)", (name, layout.get("type","zfs"), json.dumps(layout)))
        self.conn.commit()
        return {"created": True, "pool": name}

    def _build_zpool_cmd(self, name, layout):
        base = ["zpool","create","-f",name]
        t = layout.get("type","single")
        devs = layout.get("devices", [])
        if t == "single":
            base += devs
        elif t == "mirror":
            base += ["mirror"] + devs
        elif t.startswith("raidz"):
            base += [t] + devs
        else:
            base += devs
        return base

    def destroy_pool(self, name: str, force: bool=False) -> Dict[str, Any]:
        import subprocess
        p = subprocess.run(["zpool","destroy","-f",name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            return {"deleted": False, "error": p.stderr}
        cur = self.conn.cursor()
        cur.execute("DELETE FROM pools WHERE name=?", (name,))
        self.conn.commit()
        return {"deleted": True}

    def list_datasets(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        # Try zfs list first; fallback to db
        import subprocess
        try:
            out = subprocess.check_output(["zfs","list","-H","-o","name,mountpoint"]).decode()
            res = []
            for line in out.splitlines():
                name,mount = line.split("\t")
                if pool and not name.startswith(pool+"/"): continue
                res.append({"name": name, "mountpoint": mount, "pool": name.split("/")[0]})
            return res
        except Exception:
            cur = self.conn.cursor()
            if pool:
                cur.execute("SELECT name,data FROM datasets WHERE pool=?", (pool,))
            else:
                cur.execute("SELECT pool,name,data FROM datasets")
            rows = cur.fetchall()
            out = []
            for r in rows:
                d = dict(r)
                if d.get("data"):
                    try: d.update(json.loads(d["data"]))
                    except: pass
                out.append(d)
            return out

    def create_dataset(self, pool: str, name: str, mountpoint: Optional[str]=None) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO datasets (pool,name,data) VALUES (?,?,?)", (pool,name,json.dumps({"mountpoint": mountpoint})))
        self.conn.commit()
        return {"created": True, "dataset": f"{pool}/{name}"}

    def destroy_dataset(self, pool: str, name: str, recursive: bool=False) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM datasets WHERE pool=? AND name=?", (pool, name))
        self.conn.commit()
        return {"deleted": True}

    # snapshots - naive DB-backed (zfs snapshots should be used if available)
    def list_snapshots(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        return []

    def create_snapshot(self, dataset: str, snapshot_name: str) -> Dict[str, Any]:
        # attempt zfs snapshot if available
        import subprocess
        try:
            p = subprocess.run(["zfs","snapshot", f"{dataset}@{snapshot_name}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                return {"error": p.stderr}
            return {"created": True}
        except Exception as e:
            return {"error": str(e)}

    def destroy_snapshot(self, snapshot: str) -> Dict[str, Any]:
        import subprocess
        try:
            p = subprocess.run(["zfs","destroy", snapshot], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                return {"error": p.stderr}
            return {"deleted": True}
        except Exception as e:
            return {"error": str(e)}

    # shares, acls, smart, ping minimal implementations:
    def list_shares(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT name,data FROM shares")
        return [dict(r) for r in cur.fetchall()]

    def create_share(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO shares (name,data) VALUES (?,?)", (meta["name"], json.dumps(meta)))
        self.conn.commit()
        return {"created": True}

    def delete_share(self, name: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM shares WHERE name=?", (name,))
        self.conn.commit()
        return {"deleted": True}

    def list_acls(self, path: str) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT username,data FROM acls WHERE path=?", (path,))
        return [dict(r) for r in cur.fetchall()]

    def set_acl(self, path: str, acl: List[Dict[str, Any]]) -> Dict[str, Any]:
        cur = self.conn.cursor()
        for entry in acl:
            cur.execute("INSERT INTO acls (path,username,data) VALUES (?,?,?)", (path, entry["username"], json.dumps(entry)))
        self.conn.commit()
        return {"updated": True}

    def remove_acl(self, path: str, username: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM acls WHERE path=? AND username=?", (path, username))
        self.conn.commit()
        return {"removed": True}

    def smart_health(self, devpath: str) -> Dict[str, Any]:
        import subprocess, json
        try:
            p = subprocess.run(["smartctl","-a","-j", devpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                return {"error": p.stderr}
            return json.loads(p.stdout)
        except Exception as e:
            return {"error": str(e)}

    def ping(self) -> Dict[str, Any]:
        return {"ok": True, "backend": "sqlite"}
