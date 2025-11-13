from fastapi import APIRouter
import psutil

router = APIRouter()

@router.post("/metrics")
def metrics():
    return {
        "response": {
            "cpu": psutil.cpu_percent(0.1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent
        },
        "error": None
    }
