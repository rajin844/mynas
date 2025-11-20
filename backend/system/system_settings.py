import os

"""
General NAS system settings
"""

def set_hostname(name):
    print(f"Setting NAS hostname to '{name}'")

def get_hostname():
    return "MyNAS"

def enable_service(service_name):
    print(f"Enabling service '{service_name}'")

def disable_service(service_name):
    print(f"Disabling service '{service_name}'")

def list_services():
    return {
        "smbd": "active",
        "nfs-server": "inactive",
        "ssh": "active"
    }

def schedule_task(task_name, function, time_or_interval):
    print(f"Scheduling task '{task_name}' at {time_or_interval}")

def monitor_storage():
    return {
        "total_space": "2TB",
        "used": "1TB",
        "free": "1TB"
    }
