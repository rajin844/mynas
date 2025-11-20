from backend.app.json_driver import JSONDriver
from backend.app.storage_driver import StorageDriver
from typing import Dict, Any

class ConfigManager:
    def __init__(self, driver: StorageDriver = None):
        self.driver = driver or JSONDriver()
        self.reload()

    def reload(self):
        self.data = self.driver.load_all()
        return self.data

    def save(self, data=None):
        if data:
            self.data = data
        self.driver.save_all(self.data)

    # SECTION API
    def get(self, section: str):
        return self.driver.get_section(section)

    def set(self, section: str, value: Any):
        self.driver.update_section(section, value)

# Global instance
cfg = ConfigManager()
