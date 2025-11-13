from fastapi import APIRouter
import psutil, socket

router = APIRouter()

@router.post("/listinterfaces")
def list_ifaces():
    addrs = psutil.net_if_addrs()
    result = {iface: [a.address for a in lst if hasattr(a, "address")] for iface, lst in addrs.items()}
    return {"response": result, "error": None}

@router.post("/hostname")
def host():
    return {"response": socket.gethostname(), "error": None}
