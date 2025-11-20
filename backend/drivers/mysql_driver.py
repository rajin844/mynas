# backend/drivers/mysql_driver.py
import os
import json
import subprocess
from typing import List, Dict, Any, Optional
import pymysql
from pymysql.err import OperationalError

# env defaults
DB_HOST = os.environ.get("MYNAS_MYSQL_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("MYNAS_MYSQL_PORT", "3306"))
DB_USER = os.environ.get("MYNAS_MYSQL_USER", "mynas")
DB_PASS = os.environ.get("MYNAS_MYSQL_PASS", "mynas")
DB_NAME = os.environ.get("MYNAS_MYSQL_DB", "mynas")
DB_CHARSET = "utf8mb4"

def _conn():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=True,
        charset=DB_CHARSET,
        cursorclass=pymysql.cursors.DictCursor,
    )

class MySQLDriver:
    def __init__(self, cfg=None):
        self.cfg = cfg
        # ensure DB exists: caller should run migrate.py; if not, we attempt to create tables
        try:
            with _conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
        except OperationalError as e:
            raise RuntimeError("MySQL connection failed: " + str(e))

    # helper to run commands
    def _run(self, cmd: List[str]) -> Dict[str, Any]:
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return {"rc": p.returncode, "out": p.stdout, "err": p.stderr}
        except Exception as e:
            return {"rc": 1, "out": "", "err": str(e)}

    # ---------- disks ----------
    def list_disks(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["lsblk","-J","-o","NAME,KNAME,SIZE,MODEL,ROTA,MOUNTPOINT,TYPE"]).decode()
            j = json.loads(out)
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
            # fallback to empty
            return []

    # ---------- pools ----------
    def list_pools(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["zpool","list","-H","-o","name,size,health"]).decode()
            rows = []
            for l in out.splitlines():
                parts = l.split()
                rows.append({"name": parts[0], "size": parts[1] if len(parts) > 1 else None, "health": parts[2] if len(parts) > 2 else "UNKNOWN"})
            return rows
        except Exception:
            with _conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT name, type, data FROM pools")
                    res = []
                    for r in cur.fetchall():
                        d = {"name": r["name"], "type": r["type"]}
                        if r.get("data"):
                            try: d.update(json.loads(r["data"]))
                            except: pass
                        res.append(d)
                    return res

    def create_pool(self, name: str, layout: Dict[str, Any], dry_run: bool=False, run_async: bool=False) -> Dict[str, Any]:
        """
        If dry_run: return preview
        If run_async: caller should enqueue background job (task queue). This method still supports direct create.
        """
        t = layout.get("type", "single")
        devices = layout.get("devices", [])

        # build command
        cmd = ["zpool", "create", "-n", name] if dry_run else ["zpool", "create", "-f", name]
        if t == "single":
            cmd += devices
        elif t == "mirror":
            cmd += ["mirror"] + devices
        elif t.startswith("raidz"):
            cmd += [t] + devices
        else:
            cmd += devices

        if dry_run:
            return {"dry_run": True, "cmd_preview": cmd}

        # run actual zpool create
        res = self._run(cmd)
        if res["rc"] != 0:
            return {"created": False, "error": res["err"]}

        # persist metadata
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO pools (name, type, data) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE type=VALUES(type), data=VALUES(data)",
                    (name, t, json.dumps(layout))
                )
        return {"created": True, "pool": name}

    def destroy_pool(self, name: str, force: bool=False) -> Dict[str, Any]:
        cmd = ["zpool", "destroy", "-f", name]
        res = self._run(cmd)
        if res["rc"] != 0:
            return {"deleted": False, "error": res["err"]}
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM pools WHERE name=%s", (name,))
        return {"deleted": True}

    # ---------- datasets ----------
    def list_datasets(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["zfs","list","-H","-o","name,mountpoint"]).decode()
            rows = []
            for l in out.splitlines():
                name, mount = l.split("\t")
                if pool and not name.startswith(pool + "/"):
                    continue
                rows.append({"name": name, "mountpoint": mount})
            return rows
        except Exception:
            with _conn() as conn:
                with conn.cursor() as cur:
                    if pool:
                        cur.execute("SELECT pool,name,data FROM datasets WHERE pool=%s", (pool,))
                    else:
                        cur.execute("SELECT pool,name,data FROM datasets")
                    res = []
                    for r in cur.fetchall():
                        d = {"pool": r["pool"], "name": r["name"]}
                        if r.get("data"):
                            try: d.update(json.loads(r["data"]))
                            except: pass
                        res.append(d)
                    return res

    def create_dataset(self, pool: str, name: str, mountpoint: Optional[str]=None) -> Dict[str, Any]:
        cmd = ["zfs", "create"]
        if mountpoint:
            cmd += ["-o", f"mountpoint={mountpoint}"]
        cmd.append(f"{pool}/{name}")
        res = self._run(cmd)
        if res["rc"] != 0:
            return {"created": False, "error": res["err"]}
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO datasets (pool, name, data) VALUES (%s, %s, %s)", (pool, name, json.dumps({"mountpoint": mountpoint})))
        return {"created": True, "dataset": f"{pool}/{name}"}

    def destroy_dataset(self, pool: str, name: str, recursive: bool=False) -> Dict[str, Any]:
        args = ["zfs", "destroy"]
        if recursive:
            args += ["-r"]
        args.append(f"{pool}/{name}")
        res = self._run(args)
        if res["rc"] != 0:
            return {"deleted": False, "error": res["err"]}
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM datasets WHERE pool=%s AND name=%s", (pool, name))
        return {"deleted": True}

    # ---------- snapshots ----------
    def list_snapshots(self, pool: Optional[str]=None) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["zfs","list","-t","snapshot","-H","-o","name"]).decode()
            rows = [{"name": l.strip()} for l in out.splitlines() if (not pool or l.startswith(pool + "/"))]
            return rows
        except Exception:
            return []

    def create_snapshot(self, dataset: str, snapshot_name: str) -> Dict[str, Any]:
        res = self._run(["zfs","snapshot", f"{dataset}@{snapshot_name}"])
        if res["rc"] != 0:
            return {"created": False, "error": res["err"]}
        return {"created": True}

    def destroy_snapshot(self, snapshot: str) -> Dict[str, Any]:
        res = self._run(["zfs","destroy", snapshot])
        if res["rc"] != 0:
            return {"deleted": False, "error": res["err"]}
        return {"deleted": True}

    # ---------- shares ----------
    def list_shares(self) -> List[Dict[str, Any]]:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, data FROM shares")
                out = []
                for r in cur.fetchall():
                    d = {"name": r["name"]}
                    if r.get("data"):
                        try: d.update(json.loads(r["data"]))
                        except: pass
                    out.append(d)
                return out

    def create_share(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO shares (name, data) VALUES (%s,%s) ON DUPLICATE KEY UPDATE data=VALUES(data)", (meta["name"], json.dumps(meta)))
        return {"created": True, "share": meta}

    def delete_share(self, name: str) -> Dict[str, Any]:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM shares WHERE name=%s", (name,))
        return {"deleted": True}

    # ---------- ACLs ----------
    def list_acls(self, path: str) -> List[Dict[str, Any]]:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username, data FROM acls WHERE path=%s", (path,))
                out = []
                for r in cur.fetchall():
                    try: d = json.loads(r["data"])
                    except: d = {}
                    d["username"] = r["username"]
                    out.append(d)
                return out

    def set_acl(self, path: str, acl: List[Dict[str, Any]]) -> Dict[str, Any]:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM acls WHERE path=%s", (path,))
                for ent in acl:
                    cur.execute("INSERT INTO acls (path, username, data) VALUES (%s,%s,%s)", (path, ent["username"], json.dumps(ent)))
        return {"updated": True}

    def remove_acl(self, path: str, username: str) -> Dict[str, Any]:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM acls WHERE path=%s AND username=%s", (path, username))
        return {"removed": True}

    # ---------- SMART ----------
    def smart_health(self, devpath: str) -> Dict[str, Any]:
        try:
            p = subprocess.run(["smartctl","-a","-j", devpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                return {"error": p.stderr}
            return json.loads(p.stdout)
        except Exception as e:
            return {"error": str(e)}

    def ping(self) -> Dict[str, Any]:
        return {"ok": True, "backend": "mysql"}
