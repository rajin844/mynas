"""
backend/api/users.py
--------------------
User management REST API for MyNAS.
Handles CRUD operations for users and groups.
"""

from fastapi import APIRouter, HTTPException
from backend.app.user_manager import (
    list_users,
    create_user,
    delete_user,
    update_user,
    get_user,
)

router = APIRouter()

@router.get("/")
def api_list_users():
    """List all users."""
    return {"users": list_users()}

@router.post("/")
def api_create_user(username: str, password: str, role: str = "user"):
    """Create a new user."""
    ok = create_user(username, password, role)
    if not ok:
        raise HTTPException(status_code=400, detail=f"User {username} already exists")
    return {"status": "created", "username": username}

@router.get("/{username}")
def api_get_user(username: str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{username}")
def api_update_user(username: str, data: dict):
    ok = update_user(username, data)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "updated", "username": username}

@router.delete("/{username}")
def api_delete_user(username: str):
    ok = delete_user(username)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted", "username": username}
