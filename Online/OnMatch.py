"""
Online/OnMatch.py
Matchmaking + Online game session — kết nối server internet thật.

Đọc SERVER_URL từ Online/config.py.
"""

import pygame
import sys
import os
import math
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_SRC  = os.path.join(_ROOT, 'src')
_UI   = os.path.join(_ROOT, 'UI')
for _p in (_SRC, _UI, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from const  import *
from game   import Game
from square import Square
from move   import Move

FPS = 60

C_BG      = (18,  18,  30)
C_BORDER  = (55,  55,  85)
C_ACCENT  = (100, 160, 255)
C_TEXT    = (220, 220, 240)
C_DIM     = (120, 120, 155)
C_SUCCESS = ( 72, 199, 142)
C_ERROR   = (220,  80,  80)

# ── UCI helpers ───────────────────────────────────────────────────────────────
_COL_MAP = {'a':0,'b':1,'c':2,'d':3,'e':4,'f':5,'g':6,'h':7}

def _uci_to_move(uci):
    if not uci or len(uci) < 4:
        return None
    try:
        fc = _COL_MAP[uci[0]]; fr = ROWS - int(uci[1])
        tc = _COL_MAP[uci[2]]; tr = ROWS - int(uci[3])
    except (KeyError, ValueError):
        return None
    if not (Square.in_range(fr, fc) and Square.in_range(tr, tc)):
        return None
    return Move(Square(fr, fc), Square(tr, tc))

def _move_to_uci(move) -> str:
    cols = 'abcdefgh'
    return (f'{cols[move.initial.col]}{ROWS - move.initial.row}'
            f'{cols[move.final.col]}{ROWS - move.final.row}')


# ── Socket client ─────────────────────────────────────────────────────────────

class _SocketClient:
    """python-socketio client chạy trong thread riêng."""

    def __init__(self, server_url: str):
        import socketio as _sio
        self.sio       = _sio.Client(reconnection=False, logger=False,
                                     engineio_logger=False)
        self._url      = server_url
        self.connected = False
        self._events: list = []
        self._lock     = threading.Lock()

        @self.sio.event
        def connect():
            self.connected = True

        @self.sio.event
        def disconnect():
            self.connected = False

        for ev in ('queued', 'match_found', 'game_started', 'opponent_move',
                   'room_created', 'room_joined', 'room_updated', 'room_closed',
                   'rooms_list', 'game_over', 'error'):
            self._reg(ev)

    def _reg(self, ev):
        @self.sio.on(ev)
        def _h(data=None):
            with self._lock:
                self._events.append((ev, data or {}))

    def connect(self, timeout=8) -> bool:
        threading.Thread(target=self._run, daemon=True).start()
        deadline = time.time() + timeout
        while not self.connected and time.time() < deadline:
            time.sleep(0.05)
        return self.connected

    def _run(self):
        try:
            self.sio.connect(self._url, transports=['websocket', 'polling'])
            self.sio.wait()
        except Exception as e:
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


# ── Matchmaking ───────────────────────────────────────────────────────────────

def launch_matchmaking(surface, screen_w, screen_h, username: str,
                       on_menu=None, apply_settings=None):
    from config import SERVER_URL

    pygame.font.init()
    f_title = pygame.font.SysFont('segoeui', 26, bold=True)
    f_sub   = pygame.font.SysFont('segoeui', 15)
    f_btn   = pygame.font.SysFont('segoeui', 14, bold=True)
    f_small = pygame.font.SysFont('segoeui', 13)
    clock   = pygame.time.Clock()

    # ── kết nối server ──
    _draw_status(surface, screen_w, screen_h,
                 f'Dang ket noi {SERVER_URL}...', 0, f_title, f_sub, f_small, None)
    pygame.display.flip()

    client = _SocketClient(SERVER_URL)
    if not client.connect():
        _show_error(surface, screen_w, screen_h,
                    'Khong the ket noi server!',
                    f'Kiem tra: {SERVER_URL}', f_title, f_sub)
        if on_menu: on_menu()
        return

    # ── vào hàng đợi ──
    client.emit('join_queue', {'username': username})
    start      = time.time()
    btn_cancel = pygame.Rect(screen_w//2 - 100, screen_h//2 + 120, 200, 44)
    running    = True
    match_data = None

    while running:
        elapsed = time.time() - start

        for ev, data in client.poll():
            if ev == 'match_found':
                match_data = data
                running = False
                break
            elif ev == 'error':
                pass   # bỏ qua lỗi nhỏ

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.emit('leave_queue')
                client.disconnect()
                running = False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_m):
                client.emit('leave_queue')
                client.disconnect()
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_cancel.collidepoint(event.pos):
                    client.emit('leave_queue')
                    client.disconnect()
                    running = False

        if not running:
            break

        _draw_status(surface, screen_w, screen_h,
                     'Dang tim doi thu...', elapsed,
                     f_title, f_sub, f_small, btn_cancel)
        pygame.display.flip()
        clock.tick(FPS)

    if match_data:
        _run_online_game(
            surface, screen_w, screen_h,
            username,
            opponent   = match_data.get('opponent', 'Unknown'),
            my_color   = match_data.get('color', 'white'),
            pin        = match_data.get('pin', ''),
            client     = client,
            apply_settings = apply_settings,
        )
    elif client.connected:
        client.disconnect()

    if on_menu:
        on_menu()


# ── Online game loop ──────────────────────────────────────────────────────────

def _run_online_game(surface, screen_w, screen_h,
                     username, opponent, my_color, pin,
                     client: _SocketClient,
                     apply_settings=None):
    pygame.font.init()
    f_info  = pygame.font.SysFont('segoeui', 15, bold=True)
    f_small = pygame.font.SysFont('segoeui', 13)

    game  = Game()
    if apply_settings:
        apply_settings(game)

    dragger = game.dragger
    board   = game.board
    clock   = pygame.time.Clock()

    _show_color_announce(surface, screen_w, screen_h,
                         'Trang ♔' if my_color == 'white' else 'Den ♚')

    exit_signal = None

    while True:
        now_player = game.next_player

        # ── nhận event từ server ──
        for ev, data in client.poll():
            if ev == 'opponent_move':
                gm = _uci_to_move(data.get('uci', ''))
                if gm:
                    sq = board.squares[gm.initial.row][gm.initial.col]
                    if sq.has_piece():
                        board.calc_moves(sq.piece, gm.initial.row, gm.initial.col, bool=True)
                        if board.valid_move(sq.piece, gm):
                            captured = board.squares[gm.final.row][gm.final.col].has_piece()
                            board.move(sq.piece, gm)
                            board.set_true_en_passant(sq.piece)
                            game.play_sound(captured)
                            game.next_turn()
            elif ev == 'game_over':
                exit_signal = 'menu'
            elif ev == 'room_closed':
                exit_signal = 'menu'

        # ── pygame events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.emit('game_over', {'pin': pin, 'result': 'disconnect'})
                client.disconnect()
                return

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_m):
                    client.emit('game_over', {'pin': pin, 'result': 'disconnect'})
                    client.disconnect()
                    exit_signal = 'menu'
                    break

            if game.is_over:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    client.disconnect()
                    exit_signal = 'menu'
                    break
                continue

            if now_player != my_color:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                dragger.update_mouse(event.pos)
                r = (dragger.mouseY - BOARD_OFFSET_Y) // SQSIZE
                c = (dragger.mouseX - BOARD_OFFSET_X) // SQSIZE
                if not Square.in_range(r, c):
                    continue
                sq = board.squares[r][c]
                if sq.has_piece() and sq.piece.color == my_color:
                    board.calc_moves(sq.piece, r, c, bool=True)
                    dragger.save_initial(event.pos)
                    dragger.drag_piece(sq.piece)

            elif event.type == pygame.MOUSEMOTION:
                r = (event.pos[1] - BOARD_OFFSET_Y) // SQSIZE
                c = (event.pos[0] - BOARD_OFFSET_X) // SQSIZE
                if Square.in_range(r, c):
                    game.set_hover(r, c)
                if dragger.dragging:
                    dragger.update_mouse(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if dragger.dragging:
                    dragger.update_mouse(event.pos)
                    r = (dragger.mouseY - BOARD_OFFSET_Y) // SQSIZE
                    c = (dragger.mouseX - BOARD_OFFSET_X) // SQSIZE
                    if Square.in_range(r, c):
                        mv = Move(Square(dragger.initial_row, dragger.initial_col),
                                  Square(r, c))
                        if board.valid_move(dragger.piece, mv):
                            captured = board.squares[r][c].has_piece()
                            board.move(dragger.piece, mv)
                            board.set_true_en_passant(dragger.piece)
                            game.play_sound(captured)
                            game.next_turn()
                            client.emit('move', {
                                'pin':      pin,
                                'uci':      _move_to_uci(mv),
                                'username': username,
                            })
                dragger.undrag_piece()

        if exit_signal:
            break

        # ── draw ──
        surface.fill((18, 18, 30))
        game.show_bg(surface)
        game.show_last_move(surface)
        game.show_moves(surface)
        game.show_pieces(surface)
        game.show_hover(surface)
        game.show_check(surface)
        if dragger.dragging:
            dragger.update_blit(surface, game._img_cache)
        game.show_turn_panel(surface)
        game.show_sidebar(surface)
        game.show_alert(surface)
        _draw_hud(surface, screen_w, screen_h,
                  username, opponent, my_color, now_player, f_info, f_small)
        if game.is_over:
            game.show_gameover(surface)
            hint = f_small.render('Bam ESC de ve menu', True, C_DIM)
            surface.blit(hint, hint.get_rect(centerx=screen_w//2, y=screen_h - 30))

        pygame.display.flip()
        clock.tick(FPS)

    if client.connected:
        client.disconnect()


# ── UI helpers ────────────────────────────────────────────────────────────────

def _draw_status(surface, sw, sh, msg, elapsed, f_title, f_sub, f_small, btn_cancel):
    surface.fill(C_BG)
    lbl = f_title.render(msg, True, C_ACCENT)
    surface.blit(lbl, lbl.get_rect(center=(sw//2, sh//2 - 80)))

    if elapsed > 0:
        t_lbl = f_sub.render(f'Thoi gian cho: {int(elapsed)}s', True, C_DIM)
        surface.blit(t_lbl, t_lbl.get_rect(center=(sw//2, sh//2 - 35)))

    # spinner
    cx, cy = sw//2, sh//2 + 30
    t = elapsed * 3
    for i in range(8):
        rad = math.radians(i * 45 + t * 60)
        sx  = cx + int(22 * math.cos(rad))
        sy  = cy + int(22 * math.sin(rad))
        s   = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(s, (*C_ACCENT, int(255 * i / 8)), (4, 4), 4)
        surface.blit(s, (sx - 4, sy - 4))

    if btn_cancel:
        mouse = pygame.mouse.get_pos()
        bc = (90, 55, 55) if btn_cancel.collidepoint(mouse) else (60, 38, 38)
        pygame.draw.rect(surface, bc, btn_cancel, border_radius=10)
        pygame.draw.rect(surface, C_BORDER, btn_cancel, 1, border_radius=10)
        cl = f_small.render('Huy tim tran', True, C_TEXT)
        surface.blit(cl, cl.get_rect(center=btn_cancel.center))


def _show_error(surface, sw, sh, line1, line2, f_title, f_sub):
    surface.fill(C_BG)
    l1 = f_title.render(line1, True, C_ERROR)
    l2 = f_sub.render(line2, True, C_DIM)
    surface.blit(l1, l1.get_rect(center=(sw//2, sh//2 - 25)))
    surface.blit(l2, l2.get_rect(center=(sw//2, sh//2 + 15)))
    hint = f_sub.render('Nhan phim bat ky de quay lai...', True, C_DIM)
    surface.blit(hint, hint.get_rect(center=(sw//2, sh//2 + 55)))
    pygame.display.flip()
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        clock.tick(30)


def _show_color_announce(surface, sw, sh, label):
    f_big = pygame.font.SysFont('segoeui', 36, bold=True)
    start = time.time()
    clock = pygame.time.Clock()
    while time.time() - start < 2.0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        surface.fill(C_BG)
        t     = time.time() - start
        alpha = int(255 * min(1.0, (2.0 - t) * 2))
        lbl   = f_big.render(f'Ban choi: {label}', True, C_ACCENT)
        lbl.set_alpha(alpha)
        surface.blit(lbl, lbl.get_rect(center=(sw//2, sh//2)))
        pygame.display.flip()
        clock.tick(60)


def _draw_hud(surface, sw, sh, me, opp, my_color, now_player, f_info, f_small):
    pad = 10
    bg  = pygame.Surface((280, 60), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 130))
    surface.blit(bg, (pad, pad))

    me_c  = C_ACCENT if now_player == my_color else C_DIM
    opp_c = C_ACCENT if now_player != my_color else C_DIM
    mc    = '♔' if my_color == 'white' else '♚'
    oc    = '♚' if my_color == 'white' else '♔'

    me_s  = f_info.render(f'{mc} {me} (ban)', True, me_c)
    opp_s = f_small.render(f'{oc} {opp}', True, opp_c)
    surface.blit(me_s,  (pad + 8, pad + 6))
    surface.blit(opp_s, (pad + 8, pad + 30))

    if now_player == my_color:
        ts = f_small.render('▶ Luot cua ban', True, C_SUCCESS)
    else:
        ts = f_small.render('⏳ Cho doi thu...', True, C_DIM)
    surface.blit(ts, (pad + 8 + me_s.get_width() + 10, pad + 8))
