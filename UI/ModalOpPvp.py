"""
UI/ModalOpPvp.py
Modal tuỳ chỉnh trận PVP — kết nối Railway server thật.
  - Tạo phòng mới → server sinh PIN
  - Tìm phòng bằng PIN → join qua socket
  - Danh sách phòng lấy từ server
"""

import pygame
import os
import sys
import threading
import time

_HERE   = os.path.dirname(os.path.abspath(__file__))
_ONLINE = os.path.join(os.path.dirname(_HERE), 'Online')
for _p in (_HERE, _ONLINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_ACCENT_HOV,
    C_TEXT, C_TEXT_DIM, C_OVERLAY, C_SUCCESS, C_ERROR,
    InputField, Button,
)
from OnMatch import _SocketClient

C_CREATE_BG  = ( 50, 160, 100)
C_CREATE_HOV = ( 70, 200, 130)
C_JOIN_BG    = ( 60, 130, 220)
C_JOIN_HOV   = ( 90, 160, 255)
C_ROOM_ROW_A = ( 28,  28,  48)
C_ROOM_ROW_B = ( 34,  34,  56)


class ModalOpPvp:
    W, H = 520, 520

    def __init__(self, screen_w, screen_h, username='Guest', display_name=''):
        self.screen_w     = screen_w
        self.screen_h     = screen_h
        self.username     = username
        self.display_name = display_name or username
        self._result      = ...
        self._open_t      = 0
        self._msg         = ''
        self._msg_ok      = False

        # socket client
        self._client: _SocketClient | None = None
        self._my_pin   = None
        self._rooms    = []      # list từ server
        self._connected = False
        self._connecting = True

        self._init_fonts()
        self._build()
        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

        # kết nối server trong thread
        threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        from server_config import SERVER_URL
        c = _SocketClient(SERVER_URL)
        if c.connect(timeout=8):
            self._client    = c
            self._connected = True
            c.emit('get_rooms')
        else:
            self._msg    = 'Khong the ket noi server!'
            self._msg_ok = False
        self._connecting = False

    def _init_fonts(self):
        self.f_title = pygame.font.SysFont('segoeui', 19, bold=True)
        self.f_label = pygame.font.SysFont('segoeui', 13)
        self.f_input = pygame.font.SysFont('segoeui', 15)
        self.f_btn   = pygame.font.SysFont('segoeui', 14, bold=True)
        self.f_room  = pygame.font.SysFont('segoeui', 13)
        self.f_pin   = pygame.font.SysFont('segoeui', 26, bold=True)
        self.f_small = pygame.font.SysFont('segoeui', 11)

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)
        pad = 28
        iw  = self.W - pad * 2
        self.btn_close = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)
        self.field_pin = InputField(
            mx + pad, my + 72, iw - 110, 40,
            label='Ma PIN phong', placeholder='6 chu so...')
        self.btn_join = Button(
            mx + pad + iw - 100, my + 72, 100, 40,
            text='Vao phong', bg=C_JOIN_BG, bg_hover=C_JOIN_HOV,
            text_color=(255,255,255), radius=10)
        self.btn_create = Button(
            mx + pad, my + 148, iw, 44,
            text='+ Tao phong moi', bg=C_CREATE_BG, bg_hover=C_CREATE_HOV,
            text_color=(255,255,255), radius=12)
        self._list_rect = pygame.Rect(mx + pad, my + 230, iw, self.H - 230 - 20)

    # ── run ───────────────────────────────────────────────────────────────────

    def run(self, surface):
        self._result = ...
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        while self._result is ...:
            # poll socket events
            if self._client:
                for ev, data in self._client.poll():
                    if ev == 'room_created':
                        self._my_pin = data.get('pin', '')
                        self._msg    = f'Phong tao: {self._my_pin}'
                        self._msg_ok = True
                        self._client.emit('get_rooms')
                    elif ev == 'room_joined':
                        pin  = data.get('pin', '')
                        host = data.get('host', '')
                        self._result = {
                            'action': 'join', 'pin': pin,
                            'host': host, 'client': self._client,
                        }
                    elif ev == 'rooms_list':
                        self._rooms = data.get('rooms', [])
                    elif ev == 'error':
                        self._msg    = data.get('msg', 'Loi')
                        self._msg_ok = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._cleanup(); self._result = None; break
                self._handle(event)

            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)
        return self._result

    def _cleanup(self):
        if self._client and self._my_pin:
            self._client.emit('leave_room', {'pin': self._my_pin,
                                             'username': self.username})
        if self._client and self._result is None:
            self._client.disconnect()

    def _handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cleanup(); self._result = None; return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_close.collidepoint(event.pos):
                self._cleanup(); self._result = None; return
            if not self.panel_rect.collidepoint(event.pos):
                self._cleanup(); self._result = None; return
            # click row phòng
            row_h = 44
            lr = self._list_rect
            for i, room in enumerate(self._rooms[:8]):
                ry = lr.y + i * row_h
                if pygame.Rect(lr.x, ry, lr.w, row_h - 2).collidepoint(event.pos):
                    self._do_join(room['pin']); return

        self.field_pin.handle_event(event)
        if self.btn_join.handle_event(event):
            self._do_join(self.field_pin.text.strip())
        if self.btn_create.handle_event(event):
            self._do_create()

    def _do_join(self, pin):
        if not pin:
            self._msg = 'Vui long nhap ma PIN'; self._msg_ok = False; return
        if not self._client:
            self._msg = 'Chua ket noi server'; self._msg_ok = False; return
        self._client.emit('join_room', {'pin': pin, 'username': self.username})

    def _do_create(self):
        if not self._client:
            self._msg = 'Chua ket noi server'; self._msg_ok = False; return
        if self._my_pin:
            self._result = {'action': 'create', 'pin': self._my_pin,
                            'host': self.username, 'client': self._client}
            return
        self._client.emit('create_room', {'username': self.username})

    # ── draw ──────────────────────────────────────────────────────────────────

    def _draw(self, surface):
        surface.blit(self._overlay, (0, 0))
        elapsed = (pygame.time.get_ticks() - self._open_t) / 200.0
        ease    = 1 - (1 - min(1.0, elapsed)) ** 3
        ox, oy  = self.panel_rect.x, self.panel_rect.y
        if ease < 1.0:
            old = surface.get_clip()
            sw = max(1, int(self.W * ease)); sh = max(1, int(self.H * ease))
            surface.set_clip(pygame.Rect(ox+(self.W-sw)//2, oy+(self.H-sh)//2, sw, sh))
        else:
            old = None
        self._draw_panel(surface, ox, oy)
        if old is not None:
            surface.set_clip(old)

    def _draw_panel(self, surface, ox, oy):
        pr = pygame.Rect(ox, oy, self.W, self.H)
        dx = ox - self.panel_rect.x
        dy = oy - self.panel_rect.y
        sh = pygame.Surface((self.W+20, self.H+20), pygame.SRCALPHA)
        sh.fill((0,0,0,80)); surface.blit(sh, (ox-10, oy+10))
        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)
        pygame.draw.rect(surface, C_ACCENT, pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        title = self.f_title.render('Tuy chinh tran', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox+self.W//2, y=oy+14))

        # trạng thái kết nối
        if self._connecting:
            st = self.f_small.render('Dang ket noi server...', True, C_TEXT_DIM)
        elif self._connected:
            st = self.f_small.render('● Da ket noi', True, C_SUCCESS)
        else:
            st = self.f_small.render('● Mat ket noi', True, C_ERROR)
        surface.blit(st, (ox + 12, oy + 16))

        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        pad = 28
        orig = self.field_pin.rect.copy()
        self.field_pin.rect = self.field_pin.rect.move(dx, dy)
        self.field_pin.draw(surface, self.f_label, self.f_input)
        self.field_pin.rect = orig

        orig = self.btn_join.rect.copy()
        self.btn_join.rect = self.btn_join.rect.move(dx, dy)
        self.btn_join.draw(surface, self.f_small)
        self.btn_join.rect = orig

        sep_y = oy + 128
        pygame.draw.line(surface, C_BORDER, (ox+pad, sep_y), (ox+self.W-pad, sep_y), 1)
        sep_lbl = self.f_small.render('hoac', True, C_TEXT_DIM)
        surface.blit(sep_lbl, sep_lbl.get_rect(centerx=ox+self.W//2, centery=sep_y))

        orig = self.btn_create.rect.copy()
        self.btn_create.rect = self.btn_create.rect.move(dx, dy)
        self.btn_create.draw(surface, self.f_btn)
        self.btn_create.rect = orig

        if self._my_pin:
            pin_bg = pygame.Rect(ox+pad, oy+200, self.W-pad*2, 26)
            pygame.draw.rect(surface, C_PANEL2, pin_bg, border_radius=6)
            pin_lbl = self.f_label.render(
                f'Ma PIN: {self._my_pin}  (cho nguoi choi vao...)', True, C_SUCCESS)
            surface.blit(pin_lbl, pin_lbl.get_rect(center=pin_bg.center))
        elif self._msg:
            c = C_SUCCESS if self._msg_ok else C_ERROR
            ml = self.f_label.render(self._msg, True, c)
            surface.blit(ml, ml.get_rect(centerx=ox+self.W//2, y=oy+200))

        # danh sách phòng từ server
        list_y = oy + (self._list_rect.y - self.panel_rect.y)
        hdr = self.f_label.render('Phong dang mo (tu server):', True, C_TEXT_DIM)
        surface.blit(hdr, (ox+pad, list_y - 18))

        row_h  = 44
        clip_r = pygame.Rect(ox+pad, list_y, self.W-pad*2,
                             self.H-(self._list_rect.y-self.panel_rect.y)-20)
        old_clip = surface.get_clip()
        surface.set_clip(clip_r)

        if not self._rooms:
            empty = self.f_label.render('Chua co phong nao...', True, C_TEXT_DIM)
            surface.blit(empty, empty.get_rect(centerx=ox+self.W//2, y=list_y+16))
        else:
            mouse = pygame.mouse.get_pos()
            for i, room in enumerate(self._rooms[:8]):
                ry  = list_y + i * row_h
                bg  = C_ROOM_ROW_A if i%2==0 else C_ROOM_ROW_B
                row = pygame.Rect(ox+pad, ry, self.W-pad*2, row_h-2)
                if row.collidepoint(mouse): bg = (50,70,120)
                pygame.draw.rect(surface, bg, row, border_radius=6)
                pin_s = self.f_pin.render(room['pin'], True, C_ACCENT)
                surface.blit(pin_s, (row.x+12, row.centery-pin_s.get_height()//2))
                host_s = self.f_room.render(f"Host: {room['host']}", True, C_TEXT)
                surface.blit(host_s, (row.x+110, row.centery-10))
                jbtn = pygame.Rect(row.right-72, row.centery-14, 64, 28)
                jc = C_JOIN_HOV if jbtn.collidepoint(mouse) else C_JOIN_BG
                pygame.draw.rect(surface, jc, jbtn, border_radius=6)
                jl = self.f_small.render('Vao', True, (255,255,255))
                surface.blit(jl, jl.get_rect(center=jbtn.center))

        surface.set_clip(old_clip)
