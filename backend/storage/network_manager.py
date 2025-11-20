from realtime.websocket_server import WSManagerProxy
import os

def update_interface(name, ip):
    WSManagerProxy.broadcast({'module':'network','action':'update','interface':name,'ip':ip})
    return True
"""
Network interface and system network settings
"""

def list_interfaces():
    return ["eth0", "eth1", "wlan0"]

def get_ip(interface):
    return "192.168.1.2"

def set_static_ip(interface, ip, gateway, dns=None):
    print(f"Setting static IP {ip} on {interface}, gateway {gateway}, dns {dns}")

def restart_network():
    print("Restarting network service")
