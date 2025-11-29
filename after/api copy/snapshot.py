# backend/api/snapshot.py
from fastapi import APIRouter, HTTPException, Body
from backend.storage.snapshot_manager import (
    list_snapshots,
    create_snapshot,
    destroy_snapshot,
    rollback_snapshot,
    clone_snapshot,
)

router = APIRouter()

@router.post("/list")
def api_snapshot_list(payload: dict = Body(None)):
    dataset = payload.get("dataset") if payload else None
    try:
        return {"response": list_snapshots(dataset), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/create")
def api_create_snapshot(payload: dict = Body(...)):
    dataset = payload.get("dataset")
    snap = payload.get("name")

    if not dataset or not snap:
        raise HTTPException(400, "dataset + name required")

    try:
        return {"response": create_snapshot(dataset, snap), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/destroy")
def api_destroy_snapshot(payload: dict = Body(...)):
    dataset = payload.get("dataset")
    snap = payload.get("name")

    if not dataset or not snap:
        raise HTTPException(400, "dataset + name required")

    try:
        return {"response": destroy_snapshot(dataset, snap), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/rollback")
def api_rollback_snapshot(payload: dict = Body(...)):
    dataset = payload.get("dataset")
    snap = payload.get("name")

    if not dataset or not snap:
        raise HTTPException(400, "dataset + name required")

    try:
        return {"response": rollback_snapshot(dataset, snap), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/clone")
def api_clone_snapshot(payload: dict = Body(...)):
    dataset = payload.get("dataset")
    snap = payload.get("name")
    target = payload.get("target")

    if not dataset or not snap or not target:
        raise HTTPException(400, "dataset + name + target required")

    try:
        return {"response": clone_snapshot(dataset, snap, target), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
