import os
from backend.permissions import apply_posix_acl, remove_posix_acl

def set_acl(path, username, permissions):
    return apply_posix_acl(path, username, permissions)

def remove_acl(path, username):
    return remove_posix_acl(path, username)

"""
Manage ACLs for datasets
"""

def set_acl(dataset, user_or_group, permission):
    """
    Set ACL for user or group on dataset
    permission: 'read', 'write', 'full'
    """
    print(f"Setting ACL on {dataset} for {user_or_group}: {permission}")

def remove_acl(dataset, user_or_group):
    print(f"Removing ACL on {dataset} for {user_or_group}")

def list_acls(dataset):
    return {
        "admin": "full",
        "user1": "read"
    }
