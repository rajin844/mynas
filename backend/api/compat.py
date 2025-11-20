# backend/api/compat.py
from fastapi import APIRouter, Request, HTTPException
from backend.rpc_handlers.rpc_server import _RPC_REGISTRY

router = APIRouter()

@router.post("/{service}/{method}")
async def compat_handler(service: str, method: str, request: Request):
    service = service.lower()
    method = method.lower()

    if service not in _RPC_REGISTRY:
        raise HTTPException(404, f"Service '{service}' not found")

    if method not in _RPC_REGISTRY[service]:
        raise HTTPException(404, f"Method '{method}' missing")

    func = _RPC_REGISTRY[service][method]

    try:
        body = await request.json()
    except:
        body = {}

    params = body.get("params", body)

    if isinstance(params, dict):
        result = func(**params)
    else:
        result = func(params)

    return {"response": result, "error": None}
