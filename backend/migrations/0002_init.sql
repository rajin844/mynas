-- For SQLite or MySQL (syntax mostly compatible; for mysql use appropriate client)
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
