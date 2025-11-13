# backend/api/compat.py
"""
Universal compatibility wrapper:
POST /api/<service>/<method>
maps to RPC handler service.method

Ex:
POST /api/zfs/listpools
POST /api/storage/list_pools
POST /api/backup/list
→ calls RPC automatically
"""

from fastapi import APIRouter, Request, HTTPException
from backend.rpc_handlers.rpc_server import get_services

router = APIRouter()

@router.post("/{service}/{method}")
async def compat_handler(service: str, method: str, request: Request):
    services = get_services()

    if service not in services:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    if method not in services[service]:
        raise HTTPException(status_code=404, detail=f"Method '{method}' not found")

    func = services[service][method]

    body = {}
    try:
        body = await request.json()
    except:
        pass

    if callable(func):
        try:
            result = func(**body) if body else func()
            return {"response": result, "error": None}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=500, detail="Invalid RPC function")
