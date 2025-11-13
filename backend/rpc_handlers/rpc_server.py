"""
backend/rpc_handlers/rpc_server.py
----------------------------------
JSON-RPC dispatcher for MyNAS.
Automatically loads all RPC handler modules under backend/rpc_handlers/.
"""

import os
import pkgutil
import importlib
import logging
import inspect
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("mynas.rpc")

router = APIRouter()


# Global registry
_services = {}

# Path to rpc_handlers package
PACKAGE_DIR = os.path.dirname(__file__)
PACKAGE_NAME = "backend.rpc_handlers"


def get_services():
    return _services


# ---------------------------------------------------------
# Registration
# ---------------------------------------------------------
def register(service: str, methods: dict):
    _services[service] = methods
    logger.info(f"RPC registered: {service} ({len(methods)} methods)")


# ---------------------------------------------------------
# Auto-load RPC modules
# ---------------------------------------------------------
def auto_register():
    """
    Load all Python modules in backend/rpc_handlers except rpc_server itself.
    """
    logger.info("Auto-registering RPC handlers...")

    for module_finder, module_name, is_pkg in pkgutil.iter_modules([PACKAGE_DIR]):

        if module_name in ("rpc_server", "__init__"):
            continue

        full_name = f"{PACKAGE_NAME}.{module_name}"

        try:
            module = importlib.import_module(full_name)

            if hasattr(module, "register_rpc"):
                module.register_rpc(register)
                logger.info(f"Loaded RPC module: {module_name}")

            else:
                logger.warning(f"Module {module_name} has no register_rpc()")

        except Exception as e:
            logger.error(f"Failed to import RPC handler '{module_name}': {e}")


# ---------------------------------------------------------
# RPC endpoint
# ---------------------------------------------------------
@router.post("/rpc")
async def rpc_endpoint(request: Request):
    """
    JSON-RPC endpoint.
    {
      "service": "backup",
      "method": "list",
      "params": {}
    }
    """
    try:
        payload = await request.json()

        service = payload.get("service")
        method = payload.get("method")
        params = payload.get("params", {}) or {}

        if service not in _services:
            return JSONResponse({"error": f"Unknown service '{service}'"}, status_code=404)

        methods = _services[service]

        if method not in methods:
            return JSONResponse({"error": f"Unknown method '{method}' for service '{service}'"}, status_code=404)

        func = methods[method]

        if inspect.iscoroutinefunction(func):
            result = await func(**params)
        else:
            result = func(**params)

        return JSONResponse({"response": result, "error": None})

    except Exception as e:
        logger.exception("RPC processing error:")
        return JSONResponse({"response": None, "error": str(e)})
