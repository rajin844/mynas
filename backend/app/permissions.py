# backend/app/permissions.py
import logging
from backend.app.driver_loader import driver
from backend.realtime.websocket_server import WSManagerProxy

logger = logging.getLogger("mynas.permissions")

def list_acls():
    return driver.list_acls()
# backend/system/permissions.py
from backend.drivers.driver_loader import get_driver
driver = get_driver()

def list_acls(path):
    return driver.list_acls(path)

def set_acl(path, acl):
    return driver.set_acl(path, acl)

def remove_acl(path, username):
    return driver.remove_acl(path, username)


