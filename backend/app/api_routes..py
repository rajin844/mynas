from fastapi import APIRouter
from .user_manager import UserManager
from .dataset_manager import DatasetManager
from .share_manager import ShareManager
from .backup_manager import BackupManager
from .network_manager import NetworkManager
from .permissions import PermissionsManager

router = APIRouter()

users = UserManager()
datasets = DatasetManager()
shares = ShareManager()
backup = BackupManager()
network = NetworkManager()
acl = PermissionsManager()

@router.post("/users/create")
def create_user(data: dict): return users.create_user(data["username"], data["password"])

@router.post("/datasets/create")
def create_dataset(data: dict): return datasets.create_dataset(data["name"], data["mountpoint"])

@router.post("/shares/create")
def create_share(data: dict): return shares.create_share(data["dataset"], data["type"])

@router.post("/backup/create")
def create_backup(): return backup.create_backup()

@router.post("/network/update")
def update_network(data: dict): return network.update_network(data["iface"], data["ip"])

@router.post("/acl/apply")
def apply_acl(data: dict): return acl.apply_acl(data["path"], data["username"], data["permissions"])
