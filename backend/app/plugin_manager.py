from importlib import import_module
from pathlib import Path
import logging

PLUGINS_DIR = Path(__file__).resolve().parent / "plugins"
logger = logging.getLogger("mynas.plugins")

class PluginManager:
    def __init__(self):
        self.plugins = {}

    def discover(self):
        if not PLUGINS_DIR.exists():
            return []
        return [p.stem for p in PLUGINS_DIR.glob("*.py") if p.name != "__init__.py"]

    def load(self, name: str):
        try:
            module = import_module(f"app.plugins.{name}")
            self.plugins[name] = module
            if hasattr(module, "register"):
                try:
                    module.register()
                except Exception as e:
                    logger.exception("Plugin register failed: %s", e)
            return True
        except Exception as e:
            logger.exception("Failed to load plugin %s: %s", name, e)
            return False

    def load_all(self):
        for name in self.discover():
            self.load(name)
        return list(self.plugins.keys())
