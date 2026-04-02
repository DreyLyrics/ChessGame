"""
DataSeverConfig.py
Database client — tự động chọn remote (Railway) hoặc local (SQLite).

Khi USE_REMOTE_DB = True:
    Mọi thao tác DB đều gọi REST API lên Railway server.
    Tất cả người dùng dùng chung 1 database trên cloud.

Khi USE_REMOTE_DB = False:
    Fallback về SQLite local (DataBase/db.py).

API:
    register(username, email, password)  → {'ok': bool, 'error'?: str}
    login(username, password)            → {'ok': bool, 'user'?: dict, 'error'?: str}
    get_user(username)                   → dict | None
    update_profile(username, ...)        → {'ok': bool}
    add_match(user_id, ...)              → {'ok': bool}
    get_match_history(user_id, limit)    → list[dict]

Dùng thay thế DataBase/db.py:
    import DataSeverConfig as db
    db.register(...)
    db.login(...)
"""

import os
import sys

# ── import config ─────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from AppSeverConfig import DB_API_URL, USE_REMOTE_DB, REQUEST_TIMEOUT

# ── fallback local db ─────────────────────────────────────────────────────────
_DB_DIR = os.path.join(os.path.dirname(_HERE), 'DataBase')
if _DB_DIR not in sys.path:
    sys.path.insert(0, _DB_DIR)


def _local():
    import db as _local_db
    return _local_db


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _post(endpoint: str, payload: dict) -> dict:
    """Gọi POST lên Railway API, fallback về local nếu lỗi mạng."""
    try:
        import requests
        r = requests.post(
            DB_API_URL + endpoint,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        return r.json()
    except Exception as e:
        return {'ok': False, 'error': f'Network error: {e}', '_offline': True}


def _get(endpoint: str, params: dict = None) -> dict:
    """Gọi GET lên Railway API."""
    try:
        import requests
        r = requests.get(
            DB_API_URL + endpoint,
            params=params or {},
            timeout=REQUEST_TIMEOUT
        )
        return r.json()
    except Exception as e:
        return {'ok': False, 'error': f'Network error: {e}', '_offline': True}


# ── Public API — tự động chọn remote hoặc local ───────────────────────────────

def register(username, email, password):
    if not USE_REMOTE_DB:
        return _local().register(username, email, password)
    res = _post('/register', {'username': username, 'email': email, 'password': password})
    if res.get('_offline'):
        # fallback local khi mất mạng
        return _local().register(username, email, password)
    return res


def login(username, password):
    if not USE_REMOTE_DB:
        return _local().login(username, password)
    res = _post('/login', {'username': username, 'password': password})
    if res.get('_offline'):
        return _local().login(username, password)
    return res


def get_user(username):
    if not USE_REMOTE_DB:
        return _local().get_user(username)
    res = _get('/user', {'username': username})
    if res.get('_offline') or not res.get('ok'):
        return _local().get_user(username)
    return res.get('user')


def get_user_by_id(uid):
    if not USE_REMOTE_DB:
        return _local().get_user_by_id(uid)
    res = _get('/user_by_id', {'id': uid})
    if res.get('_offline') or not res.get('ok'):
        return _local().get_user_by_id(uid)
    return res.get('user')


def update_profile(username, display_name=None, avatar_color=None, avatar_path=None):
    if not USE_REMOTE_DB:
        return _local().update_profile(username, display_name, avatar_color, avatar_path)
    payload = {'username': username}
    if display_name is not None: payload['display_name'] = display_name
    if avatar_color is not None: payload['avatar_color'] = avatar_color
    if avatar_path  is not None: payload['avatar_path']  = avatar_path
    res = _post('/update_profile', payload)
    if res.get('_offline'):
        return _local().update_profile(username, display_name, avatar_color, avatar_path)
    return res


def user_exists(username):
    if not USE_REMOTE_DB:
        return _local().user_exists(username)
    res = _get('/user_exists', {'username': username})
    if res.get('_offline'):
        return _local().user_exists(username)
    return res.get('exists', False)


def add_match(user_id, opponent, result, color, moves=0):
    if not USE_REMOTE_DB:
        return _local().add_match(user_id, opponent, result, color, moves)
    res = _post('/add_match', {
        'user_id': user_id, 'opponent': opponent,
        'result': result, 'color': color, 'moves': moves
    })
    if res.get('_offline'):
        return _local().add_match(user_id, opponent, result, color, moves)
    return res


def get_match_history(user_id, limit=20):
    if not USE_REMOTE_DB:
        return _local().get_match_history(user_id, limit)
    res = _get('/match_history', {'user_id': user_id, 'limit': limit})
    if res.get('_offline') or not res.get('ok'):
        return _local().get_match_history(user_id, limit)
    return res.get('history', [])
