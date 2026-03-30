"""
Online/ChessSever.py
Chess WebSocket Server — Flask-SocketIO
Deploy lên Railway/Render: server chạy standalone, client kết nối qua internet.

Deploy Railway:
    1. Push code lên GitHub
    2. Tạo project Railway → Deploy from GitHub
    3. Railway tự đọc Procfile và requirements.txt
    4. Copy URL Railway → paste vào Online/config.py

Chạy local để test:
    python Online/ChessSever.py

Events client → server:
    join_queue, leave_queue, create_room, join_room,
    leave_room, start_game, move, get_rooms, game_over

Events server → client:
    queued, match_found, room_created, room_joined,
    room_updated, room_closed, game_started, opponent_move,
    game_over, rooms_list, error
"""

import os
import threading
import random
import string
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s  %(message)s',
    datefmt='%H:%M:%S')
log = logging.getLogger('ChessServer')

# Railway inject PORT qua env var
PORT = int(os.environ.get('PORT', 5000))

from flask import Flask, request as freq
from flask_socketio import SocketIO, emit, join_room as sio_join, leave_room as sio_leave

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chess_secret_2024')

# eventlet hoặc gevent cho production; threading cho dev
_async_mode = 'eventlet' if os.environ.get('RAILWAY_ENVIRONMENT') else 'threading'
sio = SocketIO(app, cors_allowed_origins='*', async_mode=_async_mode,
               ping_timeout=60, ping_interval=25)

# ── State (in-memory) ─────────────────────────────────────────────────────────
_lock    = threading.Lock()
_queue   = []       # [{'sid', 'username', 'joined_at'}]
_rooms   = {}       # pin -> room dict
_clients = {}       # sid -> {'username', 'pin'}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gen_pin() -> str:
    with _lock:
        while True:
            pin = ''.join(random.choices(string.digits, k=6))
            if pin not in _rooms:
                return pin

def _room_info(pin: str) -> dict:
    r = _rooms.get(pin, {})
    return {
        'pin':     pin,
        'host':    r.get('host', ''),
        'guest':   r.get('guest', ''),
        'players': r.get('players', 0),
        'started': r.get('started', False),
    }

def _broadcast_rooms():
    with _lock:
        rooms = [_room_info(p) for p, r in _rooms.items()
                 if not r.get('started') and r.get('players', 0) < 2]
    sio.emit('rooms_list', {'rooms': rooms})

def _try_match():
    with _lock:
        if len(_queue) < 2:
            return
        p1 = _queue.pop(0)
        p2 = _queue.pop(0)
    pin    = _gen_pin()
    colors = ['white', 'black']
    random.shuffle(colors)
    with _lock:
        _rooms[pin] = {
            'pin': pin,
            'host': p1['username'], 'host_sid': p1['sid'],
            'guest': p2['username'], 'guest_sid': p2['sid'],
            'players': 2, 'started': True,
            'created': time.time(), 'moves': [],
        }
        _clients[p1['sid']]['pin'] = pin
        _clients[p2['sid']]['pin'] = pin
    log.info(f"Match {pin}: {p1['username']}({colors[0]}) vs {p2['username']}({colors[1]})")
    sio.emit('match_found', {'pin': pin, 'color': colors[0], 'opponent': p2['username']}, to=p1['sid'])
    sio.emit('match_found', {'pin': pin, 'color': colors[1], 'opponent': p1['username']}, to=p2['sid'])

def _handle_leave(sid: str, pin: str):
    with _lock:
        room = _rooms.get(pin)
        if not room:
            return
        is_host   = (room.get('host_sid') == sid)
        guest_sid = room.get('guest_sid', '')
        if is_host:
            _rooms.pop(pin, None)
        else:
            room.update({'guest': '', 'guest_sid': '', 'players': 1, 'started': False})
            guest_sid = None
    if is_host:
        sio.emit('room_closed', {'pin': pin})
        if guest_sid:
            sio.emit('room_closed', {'pin': pin}, to=guest_sid)
    else:
        sio.emit('room_updated', _room_info(pin), to=pin)
    _broadcast_rooms()


# ── Socket events ─────────────────────────────────────────────────────────────

@sio.on('connect')
def on_connect():
    with _lock:
        _clients[freq.sid] = {'username': '', 'pin': None}
    log.info(f'Connect: {freq.sid}')

@sio.on('disconnect')
def on_disconnect():
    sid = freq.sid
    with _lock:
        info = _clients.pop(sid, {})
        _queue[:] = [q for q in _queue if q['sid'] != sid]
    pin = info.get('pin')
    if pin:
        _handle_leave(sid, pin)
    log.info(f'Disconnect: {sid}')

@sio.on('join_queue')
def on_join_queue(data):
    sid      = freq.sid
    username = data.get('username', 'Guest')
    with _lock:
        if any(q['sid'] == sid for q in _queue):
            emit('error', {'msg': 'Ban dang trong hang doi'}); return
        _clients[sid]['username'] = username
        _queue.append({'sid': sid, 'username': username, 'joined_at': time.time()})
        pos = len(_queue)
    emit('queued', {'position': pos})
    threading.Thread(target=_try_match, daemon=True).start()

@sio.on('leave_queue')
def on_leave_queue(_=None):
    with _lock:
        _queue[:] = [q for q in _queue if q['sid'] != freq.sid]
    emit('queued', {'position': 0})

@sio.on('create_room')
def on_create_room(data):
    sid      = freq.sid
    username = data.get('username', 'Guest')
    pin      = _gen_pin()
    with _lock:
        _rooms[pin] = {
            'pin': pin, 'host': username, 'host_sid': sid,
            'guest': '', 'guest_sid': '', 'players': 1,
            'created': time.time(), 'started': False, 'moves': [],
        }
        _clients[sid].update({'username': username, 'pin': pin})
    sio_join(pin)
    emit('room_created', {'pin': pin})
    log.info(f'{username} created room {pin}')
    _broadcast_rooms()

@sio.on('join_room')
def on_join_room(data):
    sid      = freq.sid
    pin      = data.get('pin', '').strip()
    username = data.get('username', 'Guest')
    with _lock:
        room = _rooms.get(pin)
        if not room:
            emit('error', {'msg': f'Khong tim thay phong {pin}'}); return
        if room['players'] >= 2:
            emit('error', {'msg': 'Phong da day'}); return
        if room['started']:
            emit('error', {'msg': 'Tran da bat dau'}); return
        room.update({'guest': username, 'guest_sid': sid, 'players': 2})
        _clients[sid].update({'username': username, 'pin': pin})
    sio_join(pin)
    info = _room_info(pin)
    emit('room_joined', info)
    sio.emit('room_updated', info, to=pin)
    log.info(f'{username} joined room {pin}')
    _broadcast_rooms()

@sio.on('leave_room')
def on_leave_room(data):
    sid = freq.sid
    pin = data.get('pin', '')
    sio_leave(pin)
    with _lock:
        if sid in _clients:
            _clients[sid]['pin'] = None
    _handle_leave(sid, pin)

@sio.on('get_rooms')
def on_get_rooms(_=None):
    with _lock:
        rooms = [_room_info(p) for p, r in _rooms.items()
                 if not r.get('started') and r.get('players', 0) < 2]
    emit('rooms_list', {'rooms': rooms})

@sio.on('start_game')
def on_start_game(data):
    sid = freq.sid
    pin = data.get('pin', '')
    with _lock:
        room = _rooms.get(pin)
        if not room:
            emit('error', {'msg': 'Phong khong ton tai'}); return
        if room['host_sid'] != sid:
            emit('error', {'msg': 'Chi chu phong moi bat dau duoc'}); return
        if room['players'] < 2:
            emit('error', {'msg': 'Can 2 nguoi choi'}); return
        colors = ['white', 'black']
        random.shuffle(colors)
        room.update({'color_host': colors[0], 'color_guest': colors[1], 'started': True})
        h_sid = room['host_sid']; g_sid = room['guest_sid']
        host  = room['host'];     guest = room['guest']
    sio.emit('game_started', {'pin': pin, 'color': colors[0], 'opponent': guest}, to=h_sid)
    sio.emit('game_started', {'pin': pin, 'color': colors[1], 'opponent': host},  to=g_sid)
    log.info(f'Game started {pin}: {host}({colors[0]}) vs {guest}({colors[1]})')
    _broadcast_rooms()

@sio.on('move')
def on_move(data):
    sid = freq.sid
    pin = data.get('pin', '')
    uci = data.get('uci', '')
    with _lock:
        room = _rooms.get(pin)
        if not room:
            return
        room['moves'].append({'uci': uci, 'by': data.get('username', '')})
        opp_sid = room['guest_sid'] if room['host_sid'] == sid else room['host_sid']
    sio.emit('opponent_move', {'uci': uci}, to=opp_sid)

@sio.on('game_over')
def on_game_over(data):
    pin    = data.get('pin', '')
    result = data.get('result', 'unknown')
    with _lock:
        if pin in _rooms:
            _rooms[pin]['result'] = result
    sio.emit('game_over', {'result': result}, to=pin)
    log.info(f'Game over {pin}: {result}')


# ── HTTP endpoints ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return {'status': 'Chess server running', 'version': '2.0'}

@app.route('/status')
def status():
    with _lock:
        return {
            'rooms':   len(_rooms),
            'queue':   len(_queue),
            'clients': len(_clients),
        }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('=' * 50)
    print(f'  Chess Server  —  port {PORT}')
    print(f'  Status: http://localhost:{PORT}/status')
    print('=' * 50)
    sio.run(app, host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
