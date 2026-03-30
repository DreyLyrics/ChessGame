"""
API:
    get_bot_move(fen)  -> str | None   (UCI string, vd 'e2e4')
    quit_engine()                      (đóng Stockfish process)
    set_difficulty(elo)                (350-3000, gọi trước ván đầu)
"""

import subprocess
import os

# ── đường dẫn Stockfish ──────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)   # thư mục gốc project (ngoài Bot/)

# Thử nhiều vị trí phổ biến
_SF_CANDIDATES = [
    os.path.join(_ROOT, 'stockfish', 'stockfish-windows-x86-64-avx2.exe'),
    os.path.join(_ROOT, 'stockfish', 'stockfish-windows-x86-64.exe'),
    os.path.join(_ROOT, 'stockfish', 'stockfish.exe'),
    os.path.join(_HERE, 'stockfish', 'stockfish-windows-x86-64-avx2.exe'),
    os.path.join(_HERE, 'stockfish', 'stockfish-windows-x86-64.exe'),
    os.path.join(_HERE, 'stockfish', 'stockfish.exe'),
    'stockfish',   # nếu đã có trong PATH
]

def _find_stockfish():
    for p in _SF_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None

THINK_TIME_MS = 100   # ms — chỉnh độ khó tại đây (100 = dễ, 2000 = khó)


# ── UCI wrapper ───────────────────────────────────────────────────────────────

class StockfishUCI:
    """Giao tiếp Stockfish qua subprocess UCI."""

    def __init__(self, path, think_ms=THINK_TIME_MS):
        self._think_ms = think_ms
        self._proc = subprocess.Popen(
            path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,   # tránh output lẫn vào stdout
            text=True,
        )
        self._send('uci')
        self._wait_for('uciok')
        self._send('isready')
        self._wait_for('readyok')

    def _send(self, cmd):
        self._proc.stdin.write(cmd + '\n')
        self._proc.stdin.flush()

    def _wait_for(self, token):
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError('Stockfish process ended unexpectedly')
            if token in line:
                return line.strip()

    def get_best_move(self, fen):
        """Trả về UCI string (vd 'e2e4') hoặc None."""
        self._send('position fen ' + fen)
        self._send('go movetime ' + str(self._think_ms))
        while True:
            line = self._proc.stdout.readline()
            if not line:
                return None
            line = line.strip()
            if line.startswith('bestmove'):
                parts = line.split()
                mv = parts[1] if len(parts) > 1 else None
                return None if (mv is None or mv == '(none)') else mv

    def set_difficulty(self, elo):
        """Giới hạn ELO (350–3000)."""
        elo = max(350, min(3000, int(elo)))
        self._send('setoption name UCI_LimitStrength value true')
        self._send('setoption name UCI_Elo value ' + str(elo))

    def quit(self):
        try:
            self._send('quit')
            self._proc.wait(timeout=3)
        except Exception:
            self._proc.kill()


# ── singleton ─────────────────────────────────────────────────────────────────

_engine = None   # StockfishUCI instance, khởi động lazy


def _get_engine():
    global _engine
    if _engine is None:
        path = _find_stockfish()
        if path is None:
            raise FileNotFoundError(
                'Khong tim thay Stockfish!\n'
                'Tai ve tai: https://stockfishchess.org/download/\n'
                'Dat file vao: Bot/stockfish/stockfish.exe'
            )
        _engine = StockfishUCI(path)
    return _engine


# ── public API ────────────────────────────────────────────────────────────────

def get_bot_move(fen):
    """Nhan FEN string, tra ve UCI string tot nhat (vd 'e2e4') hoac None."""
    return _get_engine().get_best_move(fen)


def set_difficulty(elo):
    """Chinh do kho bot theo ELO (350-3000). Goi truoc khi bat dau van."""
    _get_engine().set_difficulty(elo)


def quit_engine():
    """Dong Stockfish process. Goi khi thoat game."""
    global _engine
    if _engine is not None:
        _engine.quit()
        _engine = None
