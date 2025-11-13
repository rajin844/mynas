from fastapi import APIRouter, HTTPException
from backend.app.data.models.share_model import ShareModel
from backend.storage.share_manager import add_share, list_shares

router = APIRouter()

@router.get("/")
def api_list_shares():
    return list_shares_api()

@router.post("/create")
def api_create_share(s: ShareModel):
    ok = create_share_api(s.name, s.path, s.protocol)
    if not ok:
        raise HTTPException(500, "failed to create share")
    return {"ok": True}
