"""
Online/socket_client.py
Thread-safe socket client dùng queue.Queue — không bao giờ mất event.
"""

import threading
import queue
import time
import logging

logging.getLogger('engineio.client').setLevel(logging.ERROR)
logging.getLogger('socketio.client').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)


class SocketClient:
    EVENTS = (
        'queued', 'match_found', 'game_started', 'opponent_move',
        'room_created', 'room_joined', 'room_updated', 'room_closed',
        'rooms_list', 'game_over', 'error',
    )

    def __init__(self, server_url: str):
        import socketio as _sio
        self.sio       = _sio.Client(reconnection=False, logger=False,
                                     engineio_logger=False)
        self._url      = server_url
        self.connected = False
        self._q        = queue.Queue()   # thread-safe, không bao giờ mất event

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
            self._q.put((ev, data or {}))   # put vào queue, không bao giờ mất

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
        """Lấy tất cả event hiện có, không block."""
        evs = []
        while True:
            try:
                evs.append(self._q.get_nowait())
            except queue.Empty:
                break
        return evs

    def wait_for(self, event_name: str, timeout: float = 60) -> dict | None:
        """Block cho đến khi nhận được event cụ thể. Các event khác vẫn được giữ lại."""
        deadline = time.time() + timeout
        pending  = []   # event chưa phải event cần tìm
        while time.time() < deadline:
            try:
                ev, data = self._q.get(timeout=0.1)
                if ev == event_name:
                    # đưa các event pending trở lại queue
                    for item in pending:
                        self._q.put(item)
                    return data
                else:
                    pending.append((ev, data))
            except queue.Empty:
                continue
        # timeout — đưa pending trở lại
        for item in pending:
            self._q.put(item)
        return None

    def disconnect(self):
        try:
            self.sio.disconnect()
        except Exception:
            pass
