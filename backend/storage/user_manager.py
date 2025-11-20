# backend/system/user_manager.py
from backend.drivers.driver_loader import get_driver
from backend.app.config_manager import cfg
driver = get_driver()

def list_users():
    # If driver implements user table
    if hasattr(driver, "list_users"):
        return driver.list_users()
    # fallback config
    from backend.app.config_manager import cfg
    return cfg.list_users()

def create_user(userobj):
    # driver should implement user storage if DB; else config_manager add_user
    try:
        if hasattr(driver, "create_user"):
            return driver.create_user(userobj)
        else:
            from backend.app.config_manager import cfg
            cfg.add_user(userobj)
            return {"created": True}
    except Exception as e:
        return {"error": str(e)}

def add_user(self, data: Dict[str, Any]):
        cfg.add_user(data)
        return {"created": True}        

def delete_user(username):
    if hasattr(driver, "delete_user"):
        return driver.delete_user(username)
    from backend.app.config_manager import cfg
    cfg.remove_user(username)
    return {"deleted": True}
user_manager = UserManager()            
