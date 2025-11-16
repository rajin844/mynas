# backend/rpc_handlers/rpc_server.py
"""
RPC server / registry for MyNAS.

Provides:
 - register(service, methods_dict)
 - auto_register()       -> import all backend.rpc_handlers.* modules and call register_rpc(register)
 - get_services()        -> readonly view of registry
 - APIRouter `router`    -> POST /api/rpc/{service}/{method}
"""

import pkgutil
import importlib
import logging
from typing import Callable, Dict, Any
from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger("mynas.rpc")

router = APIRouter()

# internal registry: service -> method -> callable
_RPC_REGISTRY: Dict[str, Dict[str, Callable]] = {}

def register(service: str, methods: Dict[str, Callable]) -> None:
    """
    Register a service and its methods.
    service: "zfs", methods: {"list": callable, "create": callable}
    """
    s = service.lower()
    _RPC_REGISTRY[s] = {k.lower(): v for k, v in methods.items()}
    logger.info("RPC registered: %s -> %s", s, list(_RPC_REGISTRY[s].keys()))

def get_services() -> Dict[str, Dict[str, Callable]]:
    """Return the registry (read-only view ok)."""
    return _RPC_REGISTRY

def get_services(pretty: bool = False):
    """
    Return the RPC registry.

    pretty = False → raw dict (machine-friendly)
    pretty = True  → human-friendly list for UI/debugging

    Example (pretty=True):
    [
        { "service": "zfs", "methods": ["list", "create", "destroy"] },
        { "service": "snapshot", "methods": ["list", "create", "destroy"] },
        ...
    ]
    """
    if not pretty:
        return _RPC_REGISTRY

    out = []
    for svc, methods in _RPC_REGISTRY.items():
        out.append({
            "service": svc,
            "methods": sorted(list(methods.keys())),
            "method_count": len(methods),
        })
    return out


def auto_register():
    """
    Import all modules under backend.rpc_handlers and call register_rpc(register) if present.
    This lets each handler module call register(...) to populate the registry.
    """
    logger.info("RPC: auto-registering handlers from backend.rpc_handlers")
    try:
        import backend.rpc_handlers as handlers_pkg
    except Exception as e:
        logger.exception("RPC: cannot import backend.rpc_handlers package: %s", e)
        return

    for finder, name, ispkg in pkgutil.iter_modules(handlers_pkg.__path__):
        fullname = f"backend.rpc_handlers.{name}"
        try:
            mod = importlib.import_module(fullname)
            if hasattr(mod, "register_rpc"):
                try:
                    mod.register_rpc(register)
                    logger.info("RPC: module registered -> %s", fullname)
                except Exception as e:
                    logger.exception("RPC: register_rpc failed in %s: %s", fullname, e)
            else:
                logger.debug("RPC: module has no register_rpc() -> %s", fullname)
        except Exception as e:
            logger.exception("RPC: import failed for %s: %s", fullname, e)

# -----------------------
# Dispatcher endpoint(s)
# -----------------------

@router.post("/{service}/{method}")
async def rpc_dispatch(service: str, method: str, request: Request):
    """
    POST /api/rpc/{service}/{method}
    Body may be:
      { "params": { ... } }
    or directly any json object which will be used as kwargs.
    It also accepts an array for positional params.
    """
    svc = service.lower()
    m = method.lower()

    if svc not in _RPC_REGISTRY:
        raise HTTPException(status_code=404, detail=f"RPC service '{svc}' not found")

    methods = _RPC_REGISTRY[svc]
    if m not in methods:
        raise HTTPException(status_code=404, detail=f"RPC method '{m}' not found in service '{svc}'")

    func = methods[m]

    # parse payload
    try:
        payload = {}
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        params = payload.get("params", payload)

        # call
        if isinstance(params, list):
            result = func(*params)
        elif isinstance(params, dict):
            result = func(**params)
        elif params is None or params == {}:
            result = func()
        else:
            # single positional param
            result = func(params)
        return {"response": result, "error": None}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("RPC dispatch error: %s.%s -> %s", svc, m, e)
        raise HTTPException(status_code=500, detail=str(e))

# convenience endpoint: list services
@router.get("/services")
async def rpc_services():
    return {"services": list(_RPC_REGISTRY.keys())}
