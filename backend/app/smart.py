# backend/system/smart_manager.py
from backend.drivers.driver_loader import get_driver
driver = get_driver()

def smart_health(devpath):
    return driver.smart_health(devpath)
