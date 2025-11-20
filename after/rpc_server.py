# backend/rpc_handlers/rpc_server.py
"""
Unified RPC server for MyNAS.
Auto-loads handlers from backend.rpc_handlers.* and exposes:
POST /api/rpc/{service}/{method}
"""

import pkgutil
import importlib
import logging
from typing import Callable, Dict, Any
from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger("mynas.rpc")

router = APIRouter()

# -----------------------------------------------------------------------------
# INTERNAL REGISTRY
# -----------------------------------------------------------------------------
_RPC_REGISTRY: Dict[str, Dict[str, Callable]] = {}

def register(service: str, methods: Dict[str, Callable]) -> None:
    """
    Register RPC service with methods.
    Automatically lowercases both service and method names.
    """
    svc = service.lower()
    _RPC_REGISTRY[svc] = {m.lower(): fn for m, fn in methods.items()}
    logger.info("RPC registered: %s -> %s", svc, list(_RPC_REGISTRY[svc].keys()))

# -----------------------------------------------------------------------------
# ACCESSORS
# -----------------------------------------------------------------------------
def get_services(pretty: bool = False):
    """
    pretty=False → raw registry {svc: {method: fn}}
    pretty=True  → readable list
    """
    if not pretty:
        return _RPC_REGISTRY

    return [
        {
            "service": svc,
            "methods": sorted(methods.keys()),
            "method_count": len(methods),
        }
        for svc, methods in _RPC_REGISTRY.items()
    ]

# -----------------------------------------------------------------------------
# AUTO-REGISTER HANDLERS
# -----------------------------------------------------------------------------
def auto_register():
    """
    Imports all modules in backend.rpc_handlers and calls register_rpc(register)
    """
    logger.info("RPC auto-register: scanning backend.rpc_handlers")

    try:
        import backend.rpc_handlers as pkg
    except Exception as e:
        logger.exception("Cannot load backend.rpc_handlers package: %s", e)
        return

    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        module_name = f"backend.rpc_handlers.{name}"
        try:
            mod = importlib.import_module(module_name)
            if hasattr(mod, "register_rpc"):
                mod.register_rpc(register)
                logger.info("RPC handler loaded: %s", module_name)
        except Exception as e:
            logger.exception("RPC load failed for %s: %s", module_name, e)

# -----------------------------------------------------------------------------
# RPC DISPATCH ENDPOINT
# -----------------------------------------------------------------------------
@router.post("/{service}/{method}")
async def rpc_dispatch(service: str, method: str, request: Request):
    svc = service.lower()
    meth = method.lower()

    if svc not in _RPC_REGISTRY:
        raise HTTPException(404, f"RPC service '{svc}' not found")

    if meth not in _RPC_REGISTRY[svc]:
        raise HTTPException(404, f"RPC method '{meth}' not found for service '{svc}'")

    func = _RPC_REGISTRY[svc][meth]

    # parse request body
    try:
        body = await request.json()
    except:
        body = {}

    params = body.get("params", body)

    try:
        if isinstance(params, list):
            result = func(*params)
        elif isinstance(params, dict):
            result = func(**params)
        elif not params:
            result = func()
        else:
            result = func(params)
        return {"response": result, "error": None}
    except Exception as e:
        logger.exception("RPC error: %s.%s -> %s", svc, meth, e)
        raise HTTPException(500, str(e))

# -----------------------------------------------------------------------------
# DEBUG ENDPOINT
# -----------------------------------------------------------------------------
@router.get("/services")
def rpc_services():
    return get_services(pretty=True)
