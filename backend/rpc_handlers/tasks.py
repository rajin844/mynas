# backend/rpc_handlers/tasks.py
from backend.app.task_queue import enqueue, get_task_status, cancel_task , enqueue_task, get_task, list_all_tasks

def rpc_enqueue(func_ref, *args, **kwargs):
    # Not safe to pass func_ref over RPC in raw form; use named tasks or handlers
    raise NotImplementedError("Use specific task enqueue helpers")

def rpc_enqueue_create_pool(name: str, layout: dict):
    return {"task_id": enqueue_task("create_pool", {"name": name, "layout": layout})}

def rpc_status(task_id):
    return get_task(task_id)

def rpc_cancel(task_id):
    return cancel_task(task_id)


def register_rpc(register):
    register("tasks", {
        "enqueue_create_pool": rpc_enqueue_create_pool,
        "status": rpc_status,
        "list": rpc_list
    })
