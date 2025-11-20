import json, threading, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / 'config'
CONFIG_FILE = CONFIG_DIR / 'config.json'
BACKUP_DIR = CONFIG_DIR / 'backups'
LOCK = threading.Lock()
MAX_BACKUPS = 20

class ConfigManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            self.save({'system':{}, 'storage':{'pools':[], 'datasets':[]}, 'users':[], 'shares':[], 'acl':[], 'backups':[]})

    def load(self):
        with LOCK:
            if not CONFIG_FILE.exists(): return {}
            return json.loads(CONFIG_FILE.read_text())

    def save(self, data):
        with LOCK:
            if CONFIG_FILE.exists():
                ts = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
                bk = BACKUP_DIR / f'config_{ts}.json'
                shutil.copy(CONFIG_FILE, bk)
                self._cleanup_backups()
            CONFIG_FILE.write_text(json.dumps(data, indent=2))
            return True

    def _cleanup_backups(self):
        files = sorted(BACKUP_DIR.glob('config_*.json'), reverse=True)
        for old in files[MAX_BACKUPS:]:
            try:
                old.unlink()
            except Exception:
                pass

    def list_pools(self):
        cfg = self.load()
        return cfg.get('storage', {}).get('pools', [])

    def add_pool(self, pool_obj):
        cfg = self.load()
        storage = cfg.setdefault('storage', {})
        pools = storage.setdefault('pools', [])
        if any(p.get('name') == pool_obj.get('name') for p in pools):
            raise ValueError('Pool exists')
        pools.append(pool_obj)
        self.save(cfg)

    def delete_pool(self, pool_name):
        cfg = self.load()
        pools = cfg.get('storage', {}).get('pools', [])
        pools = [p for p in pools if p.get('name') != pool_name]
        cfg['storage']['pools'] = pools
        datasets = cfg.get('storage', {}).get('datasets', [])
        cfg['storage']['datasets'] = [d for d in datasets if d.get('pool') != pool_name]
        self.save(cfg)

    def list_datasets(self):
        cfg = self.load()
        return cfg.get('storage', {}).get('datasets', [])

    def add_dataset(self, dataset_obj):
        cfg = self.load()
        datasets = cfg.setdefault('storage', {}).setdefault('datasets', [])
        if any(d.get('name') == dataset_obj.get('name') for d in datasets):
            raise ValueError('Dataset exists')
        datasets.append(dataset_obj)
        self.save(cfg)

    def delete_dataset(self, dataset_name):
        cfg = self.load()
        datasets = cfg.get('storage', {}).get('datasets', [])
        cfg['storage']['datasets'] = [d for d in datasets if d.get('name') != dataset_name]
        self.save(cfg)
