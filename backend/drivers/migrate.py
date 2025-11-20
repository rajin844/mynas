# backend/migrate.py
import argparse, sqlite3, os, sys
from pathlib import Path
from backend.app.config_manager import cfg

BASE = Path(__file__).resolve().parent
MIG_SQL = BASE / "migrations" / "0001_init.sql"

DEFAULT_SQLITE = os.environ.get("MYNAS_DB", str(BASE / "mynas.db"))

def run_sqlite(dbpath):
    os.makedirs(os.path.dirname(dbpath), exist_ok=True)
    sql = MIG_SQL.read_text()
    with sqlite3.connect(dbpath) as conn:
        cur = conn.cursor()
        for stmt in sql.split(";"):
            s = stmt.strip()
            if not s: continue
            cur.execute(s)
        conn.commit()
    print("SQLite migration applied:", dbpath)

def run_mysql(host,port,user,password,dbname):
    import pymysql
    conn = pymysql.connect(host=host, port=port, user=user, password=password, autocommit=True)
    cur = conn.cursor()
    try:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}`;")
        cur.execute(f"USE `{dbname}`;")
        sql = MIG_SQL.read_text()
        for stmt in sql.split(";"):
            s = stmt.strip()
            if not s: continue
            cur.execute(s)
        print("MySQL migration applied to DB:", dbname)
    finally:
        cur.close()
        conn.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", choices=["sqlite","mysql"], default="sqlite")
    p.add_argument("--sqlite-path", default=DEFAULT_SQLITE)
    p.add_argument("--mysql-host", default=os.environ.get("MYNAS_MYSQL_HOST","127.0.0.1"))
    p.add_argument("--mysql-port", default=int(os.environ.get("MYNAS_MYSQL_PORT","3306")))
    p.add_argument("--mysql-user", default=os.environ.get("MYNAS_MYSQL_USER","mynas"))
    p.add_argument("--mysql-pass", default=os.environ.get("MYNAS_MYSQL_PASS","mynas"))
    p.add_argument("--mysql-db", default=os.environ.get("MYNAS_MYSQL_DB","mynas"))
    args = p.parse_args()
    if args.db == "sqlite":
        run_sqlite(args.sqlite_path)
    else:
        run_mysql(args.mysql_host, args.mysql_port, args.mysql_user, args.mysql_pass, args.mysql_db)

if __name__ == "__main__":
    main()
