# backend/api/snapshot.py
from fastapi import APIRouter, Body, HTTPException
from backend.storage.snapshot_manager import list_snapshots, create_snapshot, destroy_snapshot


router = APIRouter()

def rpc_list(pool=None):
    return list_snapshots(pool)

def rpc_create(dataset, snapshot):
    return create_snapshot(dataset, snapshot)

def rpc_destroy(snapshot):
    return destroy_snapshot(snapshot)

def register_rpc(register):
    register("snapshot", {"list": rpc_list, "create": rpc_create, "destroy": rpc_destroy})    
