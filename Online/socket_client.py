"""
Online/socket_client.py
Wrapper mỏng quanh python-socketio — dùng chung cho OnMatch và ModalOpPvp.
"""

import threading
import time
import logging

logging.getLogger('engineio.client').setLevel(logging.ERROR)
logging.getLogger('socketio.client').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)


class SocketClient:
    """python-socketio client chạy trong thread riêng."""

    EVENTS = (
        'queued', 'match_found', 'game_started', 'opponent_move',
        'room_created', 'room_joined', 'room_updated', 'room_closed',
        'rooms_list', 'game_over', 'error',
    )

    def __init__(self, server_url: str):
        import socketio as _sio
        self.sio        = _sio.Client(reconnection=False, logger=False,
                                      engineio_logger=False)
        self._url       = server_url
        self.connected  = False
        self._events: list = []
        self._lock      = threading.Lock()

        @self.sio.event
        def connect():
            self.connected = True

        @self.sio.event
        def disconnect():
            self.connected = False

        for ev in self.EVENTS:
            self._reg(ev)

    def _reg(self, ev):
        @self.sio.on(ev)
        def _h(data=None):
            with self._lock:
                self._events.append((ev, data or {}))

    def connect(self, timeout=10) -> bool:
        threading.Thread(target=self._run, daemon=True).start()
        deadline = time.time() + timeout
        while not self.connected and time.time() < deadline:
            time.sleep(0.05)
        return self.connected

    def _run(self):
        try:
            self.sio.connect(self._url, transports=['polling', 'websocket'],
                             wait_timeout=10)
            self.sio.wait()
        except Exception:
            self.connected = False

    def emit(self, event, data=None):
        try:
            self.sio.emit(event, data or {})
        except Exception:
            pass

    def poll(self) -> list:
        with self._lock:
            evs = list(self._events)
            self._events.clear()
        return evs

    def disconnect(self):
        try:
            self.sio.disconnect()
        except Exception:
            pass
