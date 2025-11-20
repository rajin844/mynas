-- backend/migrations/0001_init.sql
CREATE TABLE IF NOT EXISTS pools (
  name TEXT PRIMARY KEY,
  type TEXT,
  data TEXT
);

CREATE TABLE IF NOT EXISTS datasets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pool TEXT,
  name TEXT,
  data TEXT
);

CREATE TABLE IF NOT EXISTS shares (
  name TEXT PRIMARY KEY,
  data TEXT
);

CREATE TABLE IF NOT EXISTS users (
  username TEXT PRIMARY KEY,
  data TEXT
);

CREATE TABLE IF NOT EXISTS acls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT,
  username TEXT,
  data TEXT
);

-- Tasks table for background jobs
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  type TEXT,
  payload TEXT,
  status TEXT,
  progress INTEGER,
  result TEXT,
  created_ts REAL,
  updated_ts REAL
);
