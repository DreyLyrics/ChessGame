"""
UI/ModalOpPvp.py
Modal tuỳ chỉnh trận PVP:
  - Tìm phòng bằng mã PIN
  - Tạo phòng mới (sinh PIN ngẫu nhiên)
  - Danh sách phòng đang mở (xoá khi chủ thoát)
"""

import pygame
import os
import sys
import random
import string
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_ACCENT_HOV,
    C_TEXT, C_TEXT_DIM, C_OVERLAY, C_SUCCESS, C_ERROR,
    InputField, Button,
)

C_CREATE_BG  = ( 50, 160, 100)
C_CREATE_HOV = ( 70, 200, 130)
C_JOIN_BG    = ( 60, 130, 220)
C_JOIN_HOV   = ( 90, 160, 255)
C_ROOM_ROW_A = ( 28,  28,  48)
C_ROOM_ROW_B = ( 34,  34,  56)
C_FULL_COLOR = (180,  60,  60)

# ── In-memory room registry (shared across instances in same process) ─────────
_ROOMS: dict = {}   # pin -> {'host': str, 'created': float, 'players': int}


def _gen_pin() -> str:
    while True:
        pin = ''.join(random.choices(string.digits, k=6))
        if pin not in _ROOMS:
            return pin


def create_room(host: str, host_display: str = '') -> str:
    pin = _gen_pin()
    _ROOMS[pin] = {
        'host':         host,
        'host_display': host_display or host,
        'created':      time.time(),
        'players':      1,
    }
    return pin


def close_room(pin: str):
    _ROOMS.pop(pin, None)


def join_room(pin: str) -> dict | None:
    return _ROOMS.get(pin)


def get_rooms() -> list[dict]:
    """Trả về danh sách phòng, xoá phòng quá 30 phút."""
    now = time.time()
    stale = [p for p, r in _ROOMS.items() if now - r['created'] > 1800]
    for p in stale:
        _ROOMS.pop(p, None)
    return [{'pin': p, **r} for p, r in _ROOMS.items()]


class ModalOpPvp:
    W, H = 520, 520

    def __init__(self, screen_w, screen_h, username: str = 'Guest', display_name: str = ''):
        self.screen_w    = screen_w
        self.screen_h    = screen_h
        self.username    = username
        self.display_name = display_name or username
        self._result  = ...   # None | {'action': 'join'|'create', 'pin': str}
        self._open_t  = 0
        self._msg     = ''
        self._msg_ok  = False
        self._my_pin  = None   # PIN phòng mình đang host

        self._init_fonts()
        self._build()

        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

    def _init_fonts(self):
        self.f_title  = pygame.font.SysFont('segoeui', 19, bold=True)
        self.f_label  = pygame.font.SysFont('segoeui', 13)
        self.f_input  = pygame.font.SysFont('segoeui', 15)
        self.f_btn    = pygame.font.SysFont('segoeui', 14, bold=True)
        self.f_room   = pygame.font.SysFont('segoeui', 13)
        self.f_pin    = pygame.font.SysFont('segoeui', 26, bold=True)
        self.f_small  = pygame.font.SysFont('segoeui', 11)

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)

        pad = 28
        iw  = self.W - pad * 2

        self.btn_close = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)

        # ── Tìm phòng bằng PIN ──
        self.field_pin = InputField(
            mx + pad, my + 72, iw - 110, 40,
            label='Ma PIN phong',
            placeholder='6 chu so...')

        self.btn_join = Button(
            mx + pad + iw - 100, my + 72, 100, 40,
            text='Vao phong',
            bg=C_JOIN_BG, bg_hover=C_JOIN_HOV,
            text_color=(255, 255, 255), radius=10)

        # ── Tạo phòng ──
        self.btn_create = Button(
            mx + pad, my + 148, iw, 44,
            text='+ Tao phong moi',
            bg=C_CREATE_BG, bg_hover=C_CREATE_HOV,
            text_color=(255, 255, 255), radius=12)

        # vùng danh sách phòng
        self._list_rect = pygame.Rect(mx + pad, my + 230, iw, self.H - 230 - 20)

    def run(self, surface):
        self._result = ...
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        while self._result is ...:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._cleanup()
                    self._result = None
                    break
                self._handle(event)
            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)
        return self._result

    def _cleanup(self):
        if self._my_pin:
            close_room(self._my_pin)
            self._my_pin = None

    def _handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cleanup()
            self._result = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.btn_close.collidepoint(pos):
                self._cleanup()
                self._result = None
                return
            if not self.panel_rect.collidepoint(pos):
                self._cleanup()
                self._result = None
                return

            # click vào row phòng trong danh sách
            rooms = get_rooms()
            lr = self._list_rect
            dx = self.panel_rect.x - self.panel_rect.x
            dy = self.panel_rect.y - self.panel_rect.y
            row_h = 44
            for i, room in enumerate(rooms[:8]):
                ry = lr.y + i * row_h
                row_rect = pygame.Rect(lr.x, ry, lr.w, row_h - 2)
                if row_rect.collidepoint(pos):
                    self._do_join(room['pin'])
                    return

        self.field_pin.handle_event(event)

        if self.btn_join.handle_event(event):
            self._do_join(self.field_pin.text.strip())

        if self.btn_create.handle_event(event):
            self._do_create()

    def _do_join(self, pin: str):
        if not pin:
            self._msg    = 'Vui long nhap ma PIN'
            self._msg_ok = False
            return
        room = join_room(pin)
        if room is None:
            self._msg    = f'Khong tim thay phong "{pin}"'
            self._msg_ok = False
            return
        # lưu display_name của guest vào room
        _ROOMS[pin]['guest_display'] = self.display_name
        self._cleanup()
        self._result = {'action': 'join', 'pin': pin, 'host': room['host'],
                        'host_display': room.get('host_display', room['host'])}

    def _do_create(self):
        if self._my_pin:
            self._result = {'action': 'create', 'pin': self._my_pin,
                            'host': self.username, 'host_display': self.display_name}
            return
        pin = create_room(self.username, self.display_name)
        self._my_pin = pin
        self._result = {'action': 'create', 'pin': pin,
                        'host': self.username, 'host_display': self.display_name}

    # ── draw ──────────────────────────────────────────────────────────────────

    def _draw(self, surface):
        surface.blit(self._overlay, (0, 0))
        elapsed = (pygame.time.get_ticks() - self._open_t) / 200.0
        ease    = 1 - (1 - min(1.0, elapsed)) ** 3
        ox, oy  = self.panel_rect.x, self.panel_rect.y

        if ease < 1.0:
            sw = max(1, int(self.W * ease))
            sh = max(1, int(self.H * ease))
            old = surface.get_clip()
            surface.set_clip(pygame.Rect(
                ox + (self.W - sw) // 2, oy + (self.H - sh) // 2, sw, sh))
        else:
            old = None

        self._draw_panel(surface, ox, oy)
        if old is not None:
            surface.set_clip(old)

    def _draw_panel(self, surface, ox, oy):
        pr = pygame.Rect(ox, oy, self.W, self.H)
        dx = ox - self.panel_rect.x
        dy = oy - self.panel_rect.y

        sh = pygame.Surface((self.W + 20, self.H + 20), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 80))
        surface.blit(sh, (ox - 10, oy + 10))

        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)
        pygame.draw.rect(surface, C_ACCENT,
                         pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        title = self.f_title.render('Tuy chinh tran', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox + self.W // 2, y=oy + 14))

        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        pad = 28

        # ── PIN input + nút vào phòng ──
        orig = self.field_pin.rect.copy()
        self.field_pin.rect = self.field_pin.rect.move(dx, dy)
        self.field_pin.draw(surface, self.f_label, self.f_input)
        self.field_pin.rect = orig

        orig = self.btn_join.rect.copy()
        self.btn_join.rect = self.btn_join.rect.move(dx, dy)
        self.btn_join.draw(surface, self.f_small)
        self.btn_join.rect = orig

        # ── divider ──
        sep_y = oy + 128
        pygame.draw.line(surface, C_BORDER,
                         (ox + pad, sep_y), (ox + self.W - pad, sep_y), 1)
        sep_lbl = self.f_small.render('hoac', True, C_TEXT_DIM)
        surface.blit(sep_lbl, sep_lbl.get_rect(centerx=ox + self.W // 2, centery=sep_y))

        # ── nút tạo phòng ──
        orig = self.btn_create.rect.copy()
        self.btn_create.rect = self.btn_create.rect.move(dx, dy)
        self.btn_create.draw(surface, self.f_btn)
        self.btn_create.rect = orig

        # hiện PIN phòng mình nếu đã tạo
        if self._my_pin:
            pin_bg = pygame.Rect(ox + pad, oy + 200, self.W - pad * 2, 26)
            pygame.draw.rect(surface, C_PANEL2, pin_bg, border_radius=6)
            pin_lbl = self.f_label.render(
                f'Ma PIN phong cua ban:  {self._my_pin}  (cho doi nguoi choi...)',
                True, C_SUCCESS)
            surface.blit(pin_lbl, pin_lbl.get_rect(center=pin_bg.center))

        # ── thông báo ──
        if self._msg and not self._my_pin:
            c  = C_SUCCESS if self._msg_ok else C_ERROR
            ml = self.f_label.render(self._msg, True, c)
            surface.blit(ml, ml.get_rect(centerx=ox + self.W // 2, y=oy + 200))

        # ── danh sách phòng ──
        list_y = oy + (self._list_rect.y - self.panel_rect.y)
        header = self.f_label.render('Danh sach phong dang mo:', True, C_TEXT_DIM)
        surface.blit(header, (ox + pad, list_y - 18))

        rooms = get_rooms()
        row_h = 44
        clip_r = pygame.Rect(ox + pad, list_y,
                             self.W - pad * 2,
                             self.H - (self._list_rect.y - self.panel_rect.y) - 20)
        old_clip = surface.get_clip()
        surface.set_clip(clip_r)

        if not rooms:
            empty = self.f_label.render('Chua co phong nao...', True, C_TEXT_DIM)
            surface.blit(empty, empty.get_rect(
                centerx=ox + self.W // 2, y=list_y + 16))
        else:
            for i, room in enumerate(rooms[:8]):
                ry   = list_y + i * row_h
                bg   = C_ROOM_ROW_A if i % 2 == 0 else C_ROOM_ROW_B
                row  = pygame.Rect(ox + pad, ry, self.W - pad * 2, row_h - 2)
                mouse = pygame.mouse.get_pos()
                if row.collidepoint(mouse):
                    bg = (50, 70, 120)
                pygame.draw.rect(surface, bg, row, border_radius=6)

                # PIN lớn bên trái
                pin_s = self.f_pin.render(room['pin'], True, C_ACCENT)
                surface.blit(pin_s, (row.x + 12, row.centery - pin_s.get_height() // 2))

                # host
                host_s = self.f_room.render(f"Host: {room['host']}", True, C_TEXT)
                surface.blit(host_s, (row.x + 110, row.centery - 10))

                # thời gian tạo
                age = int(time.time() - room['created'])
                age_s = self.f_small.render(
                    f"{age // 60}p {age % 60}s", True, C_TEXT_DIM)
                surface.blit(age_s, (row.x + 110, row.centery + 4))

                # nút Join nhỏ bên phải
                jbtn = pygame.Rect(row.right - 72, row.centery - 14, 64, 28)
                jc   = C_JOIN_HOV if jbtn.collidepoint(mouse) else C_JOIN_BG
                pygame.draw.rect(surface, jc, jbtn, border_radius=6)
                jl   = self.f_small.render('Vao', True, (255, 255, 255))
                surface.blit(jl, jl.get_rect(center=jbtn.center))

        surface.set_clip(old_clip)
