"""Run MyNAS v7: FastAPI backend + WebSocket + monitoring + demo sequence"""
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Import managers
from backend.config_manager import ConfigManager
from backend.user_manager import add_user, list_users, delete_user, verify_password
from backend.backup_manager import list_backups, create_config_backup, restore_config_backup
from backend.permissions import apply_posix_acl, remove_posix_acl
from backend.plugin_manager import load_all
from backend.monitoring import periodic_broadcast
from storage.storage_manager import create_pool, delete_pool
from storage.zfs_manager import create_pool as zfs_create_pool, create_dataset as zfs_create_dataset
from realtime.websocket_server import WSManager, WSManagerProxy

app = FastAPI(title='MyNAS v7')
app.add_middleware(
    CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*']
)

ws_manager = WSManager()
WSManagerProxy.register(ws_manager)

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Health
@app.get('/api/ping')
def ping():
    return {'status':'ok'}

# Users
@app.get('/api/users')
def api_list_users():
    return list_users()

@app.post('/api/users')
def api_add_user(data: dict):
    username = data.get('username'); password = data.get('password'); role = data.get('role','user')
    return add_user(username, password, role)

@app.delete('/api/users/{username}')
def api_delete_user(username: str):
    ok = delete_user(username)
    return {'deleted': ok}

@app.post('/api/users/verify')
def api_verify_user(data: dict):
    return {'valid': verify_password(data.get('username'), data.get('password'))}

# ACL
@app.post('/api/acl/apply')
def api_apply_acl(data: dict):
    return {'success': apply_posix_acl(data.get('path'), data.get('username'), data.get('permissions'))}

@app.post('/api/acl/remove')
def api_remove_acl(data: dict):
    return {'success': remove_posix_acl(data.get('path'), data.get('username'))}

# Backups
@app.get('/api/backups')
def api_list_backups():
    return {'backups': list_backups()}

@app.post('/api/backups/create')
def api_create_backup():
    return {'backup': create_config_backup()}

@app.post('/api/backups/restore')
def api_restore_backup(data: dict):
    ok = restore_config_backup(data.get('filename'))
    return {'restored': ok}

# Storage (pools/datasets)
@app.post('/api/storage/pools')
def api_create_pool(data: dict):
    name = data.get('name'); devices = data.get('devices', [])
    create_pool(name, devices)
    # also call zfs placeholder
    zfs_create_pool(name, devices)
    return {'status': 'ok', 'pool': name}

@app.delete('/api/storage/pools/{name}')
def api_delete_pool(name: str):
    delete_pool(name)
    return {'status': 'deleted', 'pool': name}

@app.post('/api/storage/datasets')
def api_create_dataset(data: dict):
    pool = data.get('pool'); name = data.get('name')
    zfs_create_dataset(pool, name)
    return {'status':'ok', 'dataset': f"{pool}/{name}"}

# Plugins
@app.get('/api/plugins')
def api_plugins():
    return {'plugins': load_all()}

async def demo_sequence():
    await asyncio.sleep(1.0)
    try:
        add_user('demo', 'demo123', 'admin')
    except Exception:
        pass
    try:
        create_pool('demo_pool', ['/tmp/demo_disk'])
    except Exception:
        pass
    try:
        zfs_create_dataset('demo_pool', 'demo_dataset')
    except Exception:
        pass

@app.on_event('startup')
async def startup():
    asyncio.create_task(periodic_broadcast(5.0))
    asyncio.create_task(demo_sequence())
    print('MyNAS v7 started: monitoring + demo sequence running')

if __name__ == '__main__':
    uvicorn.run('run_nas:app', host='0.0.0.0', port=3000)
