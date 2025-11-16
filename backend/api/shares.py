# backend/api/shares.py
from fastapi import APIRouter, HTTPException, Body
from backend.storage.share_manager import (
    list_shares,
    create_smb_share,
    create_nfs_share,
    remove_share,
    smb_status,
    nfs_status,
)

router = APIRouter()


@router.post("/list")
def api_list_shares():
    try:
        return {"response": list_shares(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/smb/create")
def api_smb_create(payload: dict = Body(...)):
    try:
        return {"response": create_smb_share(**payload), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/nfs/create")
def api_nfs_create(payload: dict = Body(...)):
    try:
        return {"response": create_nfs_share(**payload), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/delete")
def api_delete_share(uuid: str):
    try:
        return {"response": remove_share(uuid), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/smb/status")
def api_smb_status():
    try:
        return {"response": smb_status(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/nfs/status")
def api_nfs_status():
    try:
        return {"response": nfs_status(), "error": None}
    except Exception as e:
        raise HTTPException(500, str(e))
