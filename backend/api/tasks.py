# backend/api/tasks.py
from fastapi import APIRouter, Body, HTTPException
from backend.app.task_queue import enqueue_task, get_task, list_all_tasks

router = APIRouter()

@router.post("/enqueue")
def api_enqueue(payload: dict = Body(...)):
    ttype = payload.get("type")
    if not ttype:
        raise HTTPException(400, "type required")
    if ttype == "create_pool":
        name = payload.get("name")
        layout = payload.get("layout")
        if not name or not layout:
            raise HTTPException(400, "name and layout required")
        task_id = enqueue_task("create_pool", {"name": name, "layout": layout})
        return {"response": {"task_id": task_id}, "error": None}
    else:
        raise HTTPException(400, "unsupported task type")

@router.post("/status")
def api_status(payload: dict = Body(...)):
    tid = payload.get("task_id")
    if not tid:
        raise HTTPException(400, "task_id required")
    t = get_task(tid)
    return {"response": t, "error": None}

@router.post("/list")
def api_list(payload: dict = Body(None)):
    limit = 50
    if payload:
        limit = int(payload.get("limit", 50))
    return {"response": list_all_tasks(limit), "error": None}
