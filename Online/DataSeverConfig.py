"""
Online/DataSeverConfig.py
Database client — gọi REST API lên Railway server (PostgreSQL).

API:
    register(username, email, password)  → {'ok': bool, 'error'?: str}
    login(username, password)            → {'ok': bool, 'user'?: dict, 'error'?: str}
    get_user(username)                   → dict | None
    update_profile(username, ...)        → {'ok': bool}
    add_match(user_id, ...)              → {'ok': bool}
    get_match_history(user_id, limit)    → list[dict]
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from AppSeverConfig import DB_API_URL, REQUEST_TIMEOUT


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _post(endpoint: str, payload: dict) -> dict:
    try:
        import requests
        r = requests.post(DB_API_URL + endpoint, json=payload, timeout=REQUEST_TIMEOUT)
        return r.json()
    except Exception as e:
        return {'ok': False, 'error': f'Network error: {e}'}


def _get(endpoint: str, params: dict = None) -> dict:
    try:
        import requests
        r = requests.get(DB_API_URL + endpoint, params=params or {}, timeout=REQUEST_TIMEOUT)
        return r.json()
    except Exception as e:
        return {'ok': False, 'error': f'Network error: {e}'}


# ── Public API ────────────────────────────────────────────────────────────────

def register(username, email, password):
    return _post('/register', {'username': username, 'email': email, 'password': password})


def login(username, password):
    return _post('/login', {'username': username, 'password': password})


def get_user(username):
    res = _get('/user', {'username': username})
    return res.get('user') if res.get('ok') else None


def get_user_by_id(uid):
    res = _get('/user_by_id', {'id': uid})
    return res.get('user') if res.get('ok') else None


def update_profile(username, display_name=None, avatar_color=None, avatar_path=None):
    payload = {'username': username}
    if display_name is not None: payload['display_name'] = display_name
    if avatar_color is not None: payload['avatar_color'] = avatar_color
    if avatar_path  is not None: payload['avatar_path']  = avatar_path
    return _post('/update_profile', payload)


def user_exists(username):
    res = _get('/user_exists', {'username': username})
    return res.get('exists', False)


def add_match(user_id, opponent, result, color, moves=0):
    return _post('/add_match', {
        'user_id': user_id, 'opponent': opponent,
        'result': result, 'color': color, 'moves': moves
    })


def get_match_history(user_id, limit=20):
    res = _get('/match_history', {'user_id': user_id, 'limit': limit})
    return res.get('history', []) if res.get('ok') else []
