import logging
import subprocess
from subprocess import CalledProcessError, check_output, check_call
from typing import List, Dict, Optional, TypedDict

logger = logging.getLogger("mynas.zfs")
# optionally configure the logger here or configure from main app
# logging.basicConfig(level=logging.INFO)

# Stronger types for returned dicts
class PoolInfo(TypedDict):
    name: str
    health: str

class DatasetInfo(TypedDict):
    name: str
    mountpoint: str

# Helper to safely run shell commands and capture output
def _run(cmd: List[str]) -> str:
    try:
        out = check_output(cmd, stderr=subprocess.STDOUT).decode()
        return out
    except FileNotFoundError:
        logger.warning("ZFS utilities not found on system: %s", cmd[0])
        return ""
    except CalledProcessError as e:
        out = e.output.decode() if e.output else ""
        logger.error("Command failed: %s\nOutput: %s", cmd, out)
        return ""

# List imported pools
def zpool_list() -> List[PoolInfo]:
    out = _run(["zpool", "list", "-H", "-o", "name,health"])
    pools: List[PoolInfo] = []
    if not out:
        return pools
    for line in out.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # split by whitespace, but be robust if extra columns exist
        parts = line.split()
        name = parts[0]
        health = parts[1] if len(parts) > 1 else "UNKNOWN"
        pools.append({"name": name, "health": health})
    return pools

# List pools available for import
def zpool_import_list() -> List[PoolInfo]:
    """
    Parse output of `zpool import`.

    The output can be human-friendly; we look for lines that start with 'pool:' and take the pool name.
    """
    out = _run(["zpool", "import"])
    pools: List[PoolInfo] = []
    if not out:
        return pools
    pool_name: Optional[str] = None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # example: "pool: tank"
        if line.lower().startswith("pool:"):
            pool_name = line.split(":", 1)[1].strip()
            if pool_name:
                pools.append({"name": pool_name, "health": "UNKNOWN"})
    return pools

def import_pool(name: str, altroot: Optional[str] = None) -> bool:
    cmd = ["zpool", "import", name]
    if altroot:
        cmd += ["-R", altroot]
    try:
        check_call(cmd)
        logger.info("Imported ZFS pool: %s", name)
        return True
    except FileNotFoundError:
        logger.warning("zpool binary not found — mock import for %s", name)
        return True
    except CalledProcessError as e:
        logger.error("zpool import failed for %s: %s", name, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error importing pool %s: %s", name, e)
        return False

# Create a new pool
def create_pool(name: str, devices: List[str]) -> bool:
    if not devices:
        logger.error("create_pool: no devices provided for pool %s", name)
        return False
    cmd = ["zpool", "create", name] + devices
    try:
        check_call(cmd)
        logger.info("Created pool %s on devices %s", name, devices)
        return True
    except FileNotFoundError:
        logger.warning("zpool not found — mock pool creation %s", name)
        return True
    except CalledProcessError as e:
        logger.error("Failed to create pool %s: %s", name, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error creating pool %s: %s", name, e)
        return False

# Destroy pool
def destroy_pool(name: str) -> bool:
    cmd = ["zpool", "destroy", name]
    try:
        check_call(cmd)
        logger.info("Destroyed pool %s", name)
        return True
    except FileNotFoundError:
        logger.warning("zpool not found — mock destroy %s", name)
        return True
    except CalledProcessError as e:
        logger.error("Failed to destroy pool %s: %s", name, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error destroying pool %s: %s", name, e)
        return False

# Create dataset
def create_dataset(pool: str, dsname: str) -> bool:
    cmd = ["zfs", "create", f"{pool}/{dsname}"]
    try:
        check_call(cmd)
        logger.info("Created dataset %s/%s", pool, dsname)
        return True
    except FileNotFoundError:
        logger.warning("zfs not found — mock dataset creation %s/%s", pool, dsname)
        return True
    except CalledProcessError as e:
        logger.error("Failed to create dataset %s/%s: %s", pool, dsname, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error creating dataset %s/%s: %s", pool, dsname, e)
        return False

def delete_dataset(pool: str, dsname: str) -> bool:
    cmd = ["zfs", "destroy", f"{pool}/{dsname}"]
    try:
        check_call(cmd)
        logger.info("Deleted dataset %s/%s", pool, dsname)
        return True
    except FileNotFoundError:
        logger.warning("zfs not found — mock dataset deletion %s/%s", pool, dsname)
        return True
    except CalledProcessError as e:
        logger.error("Failed to delete dataset %s/%s: %s", pool, dsname, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error deleting dataset %s/%s: %s", pool, dsname, e)
        return False

# List datasets
def list_datasets() -> List[DatasetInfo]:
    out = _run(["zfs", "list", "-H", "-o", "name,mountpoint"])
    datasets: List[DatasetInfo] = []
    if not out:
        return datasets
    for line in out.strip().splitlines():
        # allow both tab-separated and multi-space separated output
        if "\t" in line:
            parts = line.split("\t")
        else:
            parts = line.split()
        if not parts:
            continue
        name = parts[0]
        mount = parts[1] if len(parts) > 1 else ""
        datasets.append({"name": name, "mountpoint": mount})
    return datasets

# Convenience helpers

def pool_exists(name: str) -> bool:
    pools = zpool_list()
    return any(p["name"] == name for p in pools)

def dataset_exists(pool: str, dsname: str) -> bool:
    ds_full = f"{pool}/{dsname}"
    for d in list_datasets():
        if d["name"] == ds_full:
            return True
    return False
