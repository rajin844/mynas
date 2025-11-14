from .config_manager import ConfigManager

class NetworkManager:
    def __init__(self):
        self.config = ConfigManager()

    def update_network(self, iface, ip):
        net = self.config.data.get("network", {})
        net[iface] = {"ip": ip}
        self.config.update_section("network", net)
        return {"status": "configured", "iface": iface, "ip": ip}
