from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.app.config_manager import ConfigManager
from backend.realtime.websocket_server import WSManagerProxy

router = APIRouter()
cfg = ConfigManager()
ws_proxy = WSManagerProxy()  # proxy that will reference the running WS manager

class PoolModel(BaseModel):
    name: str
    type: Optional[str] = "zfs"
    devices: Optional[List[str]] = []

class DatasetModel(BaseModel):
    name: str
    pool: str
    mountpoint: Optional[str] = None

@router.get("/pools")
def list_pools():
    return cfg.list_pools()

@router.post("/pools")
def create_pool(p: PoolModel):
    try:
        cfg.add_pool(p.dict())
        # notify realtime clients
        ws_proxy.broadcast({"module": "storage", "action": "create_pool", "name": p.name})
        return {"status": "ok", "pool": p.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/pools")
def delete_pool(name: str):
    cfg.delete_pool(name)
    ws_proxy.broadcast({"module": "storage", "action": "delete_pool", "name": name})
    return {"status": "ok"}

@router.get("/datasets")
def list_datasets():
    return cfg.list_datasets()

@router.post("/datasets")
def create_dataset(d: DatasetModel):
    try:
        cfg.add_dataset(d.dict())
        ws_proxy.broadcast({"module": "storage", "action": "create_dataset", "name": d.name, "pool": d.pool})
        return {"status": "ok", "dataset": d.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/datasets")
def delete_dataset(name: str):
    cfg.delete_dataset(name)
    ws_proxy.broadcast({"module": "storage", "action": "delete_dataset", "name": name})
    return {"status": "ok"}

def register_rpc(register):
    register("storage", {
        "listpools": list_pools,
        "create_pool": create_pool,
        "destroy_pool": delete_pool,
        "create_dataset": create_dataset,
        "delete dataset": delete_dataset
    })    
