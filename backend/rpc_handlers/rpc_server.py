# backend/rpc_handlers/rpc_server.py (simplified)
_services = {}

def register(service, mapping):
    _services[service] = mapping

def get_services():
    return _services

def auto_register():
    import importlib
    names = ["storage","zfs","raidz","monitor","smart","shares","snapshot","backup","tasks","users","acl","network","system","alerts"]
    for n in names:
        mod = importlib.import_module(f"backend.rpc_handlers.{n}")
        if hasattr(mod, "register_rpc"):
            mod.register_rpc(register)
