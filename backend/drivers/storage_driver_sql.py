# backend/app/storage_driver_sql.py

import sqlite3
from backend.app.storage_driver import StorageDriver

class SQLStorageDriver(StorageDriver):

    def __init__(self):
        self.conn = sqlite3.connect("/var/lib/mynas.db")

    def list_pools(self):
        cur = self.conn.execute("SELECT name, type FROM pools")
        return [dict(row) for row in cur.fetchall()]

    def save_pool(self, pool):
        self.conn.execute("INSERT INTO pools (name,type) VALUES (?,?)",
                          (pool["name"], pool["type"]))
        self.conn.commit()

    # बाकी सीधे SQL queries…
