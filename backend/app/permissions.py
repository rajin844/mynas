"""
backend/app/permissions.py
--------------------------
Extended ACL support for MyNAS

Features added:
 - Unix group ACL entries (type = "group")
 - NFSv4 advanced ACL fields (flags, scope, protocol)
 - Windows SMB rights mapping (Full Control / Modify / Read & Execute / etc.)
 - overwrite_acl_list / clear_acl (Full Rewrite Mode)
 - can_user_access(user, path, action) -> bool
 - Audit logging (uses backend.app.audit)
 - Backwards-compatible simple user:permissions entries still supported

Stored ACL entry canonical form (example):
{
  "path": "/mnt/data",
  "type": "user" | "group",
  "id": "alice" | "staff",
  "permissions": "rwx",           # basic unix-style string
  "nfs4": {                       # optional advanced NFSv4 details
    "scope": "allow",             # "allow" or "deny"
    "flags": ["file_inherit"],    # optional flags list
  },
  "protocols": ["nfs4","smb"]     # which protocols this ACL applies to (optional)
}
"""

import logging
import json
import time
from typing import Any, Dict, List, Optional

import pwd
import grp


from backend.realtime.websocket_server import WSManagerProxy
from backend.app import audit

logger = logging.getLogger("mynas.permissions")


# cfg.list_acls() returns list of entries (older code used "user" key; we support both)

# ---------------------
# helpers: normalization
# ---------------------

def _normalize_entry(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize older and newer ACL shapes into canonical shape used internally.
    Accepts legacy shapes:
      {"path":..., "user": "alice", "permissions": "rwx"}
      {"path":..., "username": "alice", "permissions": "rwx"}
    And new shapes already in canonical form.
    """
    e = dict(raw)  # shallow copy
    # unify username/user/id
    if "username" in e and "id" not in e:
        e["id"] = e.pop("username")
        e["type"] = e.get("type", "user")
    if "user" in e and "id" not in e:
        e["id"] = e.pop("user")
        e["type"] = e.get("type", "user")
    # ensure type default
    if "type" not in e:
        e["type"] = e.get("type", "user")
    # ensure permissions string
    if "permissions" not in e:
        e["permissions"] = e.get("perms", "")
    # ensure protocols
    if "protocols" not in e:
        e["protocols"] = ["nfs4", "smb"]
    # ensure nfs4 dict exists if present
    if "nfs4" in e and not isinstance(e["nfs4"], dict):
        e["nfs4"] = {}
    return e


def _entry_matches_subject(entry: Dict[str, Any], user: str, user_groups: List[str]) -> bool:
    """
    Returns True if entry applies to the user (user or one of groups).
    """
    if entry.get("type") == "user" and entry.get("id") == user:
        return True
    if entry.get("type") == "group" and entry.get("id") in user_groups:
        return True
    return False


def _rwx_to_set(perms: str) -> set:
    return set(ch for ch in perms if ch in ("r", "w", "x"))


def _map_smb_to_rwx(smb_right: str) -> str:
    """
    Map common Windows SMB rights to rwx.
    - "Full Control" -> rwx
    - "Modify" -> rw-
    - "Read & Execute" -> r-x
    - "Read" -> r--
    - "Write" -> -w-
    Unknown -> use provided string if it's already rwx-like.
    """
    s = smb_right.lower()
    if "full" in s:
        return "rwx"
    if "modify" in s:
        return "rw-"
    if "read & execute" in s or "read_execute" in s or "read-execute" in s:
        return "r-x"
    if s == "read":
        return "r--"
    if s == "write":
        return "-w-"
    # fallback: keep as-is if looks like rwx already
    if all(ch in "rwx-" for ch in smb_right):
        return smb_right
    return ""


# ---------------------
# config helpers
# ---------------------

def _load_all_acls() -> List[Dict[str, Any]]:
    raw = cfg.list_acls() or []
    return [_normalize_entry(r) for r in raw]


def _save_all_acls(all_acls: List[Dict[str, Any]]) -> None:
    # Keep backward compatibility with older callers expecting "user" key
    out = []
    for e in all_acls:
        oe = dict(e)
        # write old "user" key if type == user (backwards compatibility)
        if oe.get("type") == "user" and "user" not in oe:
            oe["user"] = oe.get("id")
        # drop ephemeral fields? leave as-is for now
        out.append(oe)
    cfg.set_section("acl", out)


# ---------------------
# Public API
# ---------------------

def list_acls() -> List[Dict[str, Any]]:
    """Return normalized ACL entries."""
    acls = _load_all_acls()
    logger.debug("Listing %d ACL entries", len(acls))
    return acls


def overwrite_acl_list(path: str, acl_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Overwrite ALL ACL entries for path.
    Input acl_list entries expected as:
      {"username": "...", "permissions": "rwx"} or
      {"type":"group","id":"staff","permissions":"r-x","nfs4":{...},"protocols":[...]}
    """
    now = time.time()
    all_acls = _load_all_acls()
    # keep entries for other paths
    filtered = [a for a in all_acls if a.get("path") != path]
    # normalize incoming
    to_add = []
    for ent in acl_list:
        normalized = _normalize_entry(ent)
        normalized["path"] = path
        to_add.append(normalized)
    filtered.extend(to_add)
    _save_all_acls(filtered)
    logger.info("ACL rewritten for path=%s entries=%d", path, len(to_add))
    WSManagerProxy.broadcast({"event": "acl_rewritten", "path": path, "count": len(to_add)})
    audit.log_event("acl_rewrite", actor="system", path=path, details={"count": len(to_add)})
    return {"status": "rewritten", "path": path, "count": len(to_add)}


def clear_acl(path: str) -> Dict[str, Any]:
    all_acls = _load_all_acls()
    before = len(all_acls)
    filtered = [a for a in all_acls if a.get("path") != path]
    removed = before - len(filtered)
    _save_all_acls(filtered)
    logger.info("ACL cleared for path=%s removed=%d", path, removed)
    WSManagerProxy.broadcast({"event": "acl_cleared", "path": path, "removed": removed})
    audit.log_event("acl_clear", actor="system", path=path, details={"removed": removed})
    return {"status": "cleared", "path": path, "removed": removed}


def set_acl_record(path: str, username: str, permissions: str) -> Dict[str, Any]:
    """
    Compatibility wrapper: set or update single user entry.
    Stores as type:user id=username
    """
    acls = _load_all_acls()
    updated = False
    for e in acls:
        if e.get("path") == path and e.get("type") == "user" and e.get("id") == username:
            e["permissions"] = permissions
            updated = True
            break
    if not updated:
        new = {"path": path, "type": "user", "id": username, "permissions": permissions}
        acls.append(new)
        _save_all_acls(acls)
        logger.info("ACL created %s", new)
        WSManagerProxy.broadcast({"event": "acl_created", "acl": new})
        audit.log_event("acl_create", actor=username, path=path, details={"permissions": permissions})
        return {"status": "created", "path": path, "user": username}
    _save_all_acls(acls)
    logger.info("ACL updated user=%s path=%s", username, path)
    WSManagerProxy.broadcast({"event": "acl_updated", "user": username, "path": path, "permissions": permissions})
    audit.log_event("acl_update", actor=username, path=path, details={"permissions": permissions})
    return {"status": "updated", "path": path, "user": username}


def delete_acl_record(path: str, username: str) -> Dict[str, Any]:
    """
    Remove single ACL entry for a user (compatibility).
    """
    acls = _load_all_acls()
    before = len(acls)
    remaining = [a for a in acls if not (a.get("path") == path and a.get("type") == "user" and a.get("id") == username)]
    removed = before - len(remaining)
    _save_all_acls(remaining)
    if removed:
        logger.info("ACL deleted user=%s path=%s", username, path)
        WSManagerProxy.broadcast({"event": "acl_deleted", "user": username, "path": path})
        audit.log_event("acl_delete", actor=username, path=path, details={})
        return {"status": "deleted", "path": path, "user": username}
    logger.warning("ACL delete not found user=%s path=%s", username, path)
    return {"status": "not_found", "path": path, "user": username}


# ---------------------
# Permission evaluation
# ---------------------

def _get_user_groups(user: str) -> List[str]:
    try:
        pw = pwd.getpwnam(user)
    except KeyError:
        return []
    groups = []
    # primary
    try:
        primary = grp.getgrgid(pw.pw_gid).gr_name
        groups.append(primary)
    except Exception:
        pass
    # supplementary
    for g in grp.getgrall():
        if user in g.gr_mem and g.gr_name not in groups:
            groups.append(g.gr_name)
    return groups


def can_user_access(user: str, path: str, action: str, protocol: Optional[str] = None) -> bool:
    """
    Evaluate whether 'user' has 'action' permission on 'path'.
    action in {"read","write","execute"}
    protocol optional: "nfs4" or "smb" or None (any)
    Rules:
      - Search ACLs for the path (exact match) — you may expand to nearest-parent lookup later
      - Entries with type=user or type=group apply
      - If an entry has protocols and protocol given, it must include it
      - Interpret SMB rights to rwx equivalents
      - NFSv4 entries with scope="deny" take precedence over allow
    Returns bool
    """
    action_map = {"read": "r", "write": "w", "execute": "x"}
    req = action_map.get(action)
    if req is None:
        raise ValueError("action must be read/write/execute")

    user_groups = _get_user_groups(user)
    entries = [e for e in _load_all_acls() if e.get("path") == path]

    # Apply DENY entries first (nfs4 scope == deny)
    for e in entries:
        if protocol and "protocols" in e and protocol not in e["protocols"]:
            continue
        if e.get("nfs4", {}).get("scope") == "deny" and _entry_matches_subject(e, user, user_groups):
            perms = e.get("permissions", "")
            if req in _rwx_to_set(perms):
                logger.debug("Access denied by NFSv4 deny entry: %s", e)
                audit.log_event("acl_check_denied", actor=user, path=path, details={"entry": e, "action": action})
                return False

    # Accumulate allows
    allowed = False
    for e in entries:
        if protocol and "protocols" in e and protocol not in e["protocols"]:
            continue
        if _entry_matches_subject(e, user, user_groups):
            # If SMB right present in e.get("smb_right"), map it
            if "smb_right" in e:
                mapped = _map_smb_to_rwx(e["smb_right"])
                perms = mapped or e.get("permissions", "")
            else:
                perms = e.get("permissions", "")
            if req in _rwx_to_set(perms):
                allowed = True
                # continue checking other denies above already handled
                break

    audit.log_event("acl_check", actor=user, path=path, details={"action": action, "allowed": allowed})
    return allowed


# ---------------------
# helper utilities for UI/backends
# ---------------------

def list_system_users(min_uid: int = 1000) -> List[Dict[str, str]]:
    """Return system users (username) for UI dropdowns. Skip system accounts by default (uid < 1000)."""
    users = []
    for p in pwd.getpwall():
        if p.pw_uid >= min_uid:
            users.append({"username": p.pw_name})
    return users


def list_system_groups(min_gid: int = 1000) -> List[Dict[str, str]]:
    groups = []
    for g in grp.getgrall():
        if g.gr_gid >= min_gid:
            groups.append({"group": g.gr_name})
    return groups
