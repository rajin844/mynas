from fastapi import APIRouter
import psutil

router = APIRouter()

@router.get("/stats")
def get_stats():
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent
    }
