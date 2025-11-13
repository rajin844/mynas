import requests
import json

API_URL = "http://localhost:8082"

def pretty(data):
    print(json.dumps(data, indent=2))

def print_menu():
    print("\n=== MyNAS CLI ===")
    print("1. List Pools")
    print("2. Create Pool")
    print("3. Delete Pool")
    print("4. List Datasets")
    print("5. Create Dataset")
    print("6. Delete Dataset")
    print("7. Manage Users")
    print("8. Manage ACL")
    print("9. Manage Backups")
    print("10. Manage Shares (Samba/NFS)")
    print("11. Show System Info")
    print("12. Exit")
    print("=================")

# ---------------- POOL + DATASET ----------------
def list_pools():
    res = requests.get(f"{API_URL}/1pools")
    pretty(res.json())

def create_pool():
    name = input("Enter pool name: ")
    size = input("Enter pool size (e.g. 100GB): ")
    data = {"name": name, "size": size}
    res = requests.post(f"{API_URL}/pools", json=data)
    pretty(res.json())

def delete_pool():
    name = input("Enter pool name to delete: ")
    res = requests.delete(f"{API_URL}/pools/{name}")
    pretty(res.json())

def list_datasets():
    res = requests.get(f"{API_URL}/datasets")
    pretty(res.json())

def create_dataset():
    pool = input("Enter pool name: ")
    name = input("Enter dataset name: ")
    data = {"pool": pool, "name": name}
    res = requests.post(f"{API_URL}/datasets", json=data)
    pretty(res.json())

def delete_dataset():
    name = input("Enter dataset name to delete: ")
    res = requests.delete(f"{API_URL}/datasets/{name}")
    pretty(res.json())

# ---------------- USERS ----------------
def manage_users():
    while True:
        print("\n--- User Management ---")
        print("1. List Users")
        print("2. Add User")
        print("3. Delete User")
        print("4. Back")
        c = input("Select: ")

        if c == "1":
            res = requests.get(f"{API_URL}/users")
            pretty(res.json())
        elif c == "2":
            username = input("Username: ")
            password = input("Password: ")
            res = requests.post(f"{API_URL}/users", json={"username": username, "password": password})
            pretty(res.json())
        elif c == "3":
            username = input("Username to delete: ")
            res = requests.delete(f"{API_URL}/users/{username}")
            pretty(res.json())
        elif c == "4":
            break
        else:
            print("Invalid choice.")

# ---------------- ACL ----------------
def manage_acl():
    while True:
        print("\n--- ACL Management ---")
        print("1. View ACLs")
        print("2. Set ACL")
        print("3. Remove ACL")
        print("4. Back")
        c = input("Select: ")

        if c == "1":
            res = requests.get(f"{API_URL}/acl")
            pretty(res.json())
        elif c == "2":
            path = input("Dataset path: ")
            user = input("Username: ")
            permission = input("Permission (read/write/admin): ")
            data = {"path": path, "user": user, "permission": permission}
            res = requests.post(f"{API_URL}/acl", json=data)
            pretty(res.json())
        elif c == "3":
            path = input("Dataset path: ")
            user = input("Username: ")
            res = requests.delete(f"{API_URL}/acl", json={"path": path, "user": user})
            pretty(res.json())
        elif c == "4":
            break
        else:
            print("Invalid choice.")

# ---------------- BACKUP ----------------
def manage_backups():
    while True:
        print("\n--- Backup Management ---")
        print("1. List Backups")
        print("2. Create Backup")
        print("3. Restore Backup")
        print("4. Delete Backup")
        print("5. Back")
        c = input("Select: ")

        if c == "1":
            res = requests.get(f"{API_URL}/backups")
            pretty(res.json())
        elif c == "2":
            name = input("Backup name: ")
            res = requests.post(f"{API_URL}/backups", json={"name": name})
            pretty(res.json())
        elif c == "3":
            name = input("Backup name to restore: ")
            res = requests.post(f"{API_URL}/backups/restore", json={"name": name})
            pretty(res.json())
        elif c == "4":
            name = input("Backup name to delete: ")
            res = requests.delete(f"{API_URL}/backups/{name}")
            pretty(res.json())
        elif c == "5":
            break
        else:
            print("Invalid choice.")

# ---------------- SHARES ----------------
def manage_shares():
    while True:
        print("\n--- Share Management ---")
        print("1. List Shares")
        print("2. Add Share (Samba/NFS)")
        print("3. Delete Share")
        print("4. Back")
        c = input("Select: ")

        if c == "1":
            res = requests.get(f"{API_URL}/shares")
            pretty(res.json())
        elif c == "2":
            name = input("Share name: ")
            path = input("Path: ")
            protocol = input("Protocol (samba/nfs): ").lower()
            data = {"name": name, "path": path, "protocol": protocol}
            res = requests.post(f"{API_URL}/shares", json=data)
            pretty(res.json())
        elif c == "3":
            name = input("Share name to delete: ")
            res = requests.delete(f"{API_URL}/shares/{name}")
            pretty(res.json())
        elif c == "4":
            break
        else:
            print("Invalid choice.")

# ---------------- SYSTEM ----------------
def system_info():
    res = requests.get(f"{API_URL}/system/info")
    pretty(res.json())

# ---------------- MAIN ----------------
def main():
    while True:
        print_menu()
        choice = input("Select option: ").strip()

        if choice == "1": list_pools()
        elif choice == "2": create_pool()
        elif choice == "3": delete_pool()
        elif choice == "4": list_datasets()
        elif choice == "5": create_dataset()
        elif choice == "6": delete_dataset()
        elif choice == "7": manage_users()
        elif choice == "8": manage_acl()
        elif choice == "9": manage_backups()
        elif choice == "10": manage_shares()
        elif choice == "11": system_info()
        elif choice == "12":
            print("Exiting CLI...")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
