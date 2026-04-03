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


# ── Friendship API ────────────────────────────────────────────────────────────

def send_friend_request(user_id: int, to_username: str) -> dict:
    return _post('/friend/send', {'user_id': user_id, 'to_username': to_username})

def accept_friend_request(user_id: int, from_user_id: int) -> dict:
    return _post('/friend/accept', {'user_id': user_id, 'from_user_id': from_user_id})

def reject_friend_request(user_id: int, from_user_id: int) -> dict:
    return _post('/friend/reject', {'user_id': user_id, 'from_user_id': from_user_id})

def remove_friend(user_id: int, friend_id: int) -> dict:
    return _post('/friend/remove', {'user_id': user_id, 'friend_id': friend_id})

def get_friends(user_id: int) -> list:
    res = _get('/friend/list', {'user_id': user_id})
    return res.get('friends', []) if res.get('ok') else []

def get_pending_requests(user_id: int) -> list:
    res = _get('/friend/pending', {'user_id': user_id})
    return res.get('requests', []) if res.get('ok') else []

def get_friendship_status(user_id: int, other_id: int) -> str:
    res = _get('/friend/status', {'user_id': user_id, 'other_id': other_id})
    return res.get('status', 'none') if res.get('ok') else 'none'


# ── Messages API ──────────────────────────────────────────────────────────────

def send_message(from_id: int, to_id: int, content: str) -> dict:
    return _post('/message/send', {'from_id': from_id, 'to_id': to_id, 'content': content})

def get_messages(user_id: int, friend_id: int, limit: int = 50) -> list:
    res = _get('/message/history', {'user_id': user_id, 'friend_id': friend_id, 'limit': limit})
    return res.get('messages', []) if res.get('ok') else []


# ── Matches (phòng chờ) ───────────────────────────────────────────────────────

def get_open_rooms() -> list:
    res = _get('/rooms')
    return res.get('rooms', []) if res.get('ok') else []


# ── Admin API ─────────────────────────────────────────────────────────────────

def admin_get_users() -> list:
    res = _get('/admin/users')
    return res.get('users', []) if res.get('ok') else []

def admin_set_role(username: str, role: str) -> dict:
    return _post('/admin/set_role', {'username': username, 'role': role})

def admin_delete_user(username: str) -> dict:
    return _post('/admin/delete_user', {'username': username})

def admin_get_messages(limit: int = 100) -> list:
    res = _get('/admin/messages', {'limit': limit})
    return res.get('messages', []) if res.get('ok') else []

def admin_delete_message(msg_id: int) -> dict:
    return _post('/admin/delete_message', {'msg_id': msg_id})
