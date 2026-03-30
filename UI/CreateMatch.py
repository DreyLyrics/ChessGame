"""
UI/CreateMatch.py
Modal phòng chờ sau khi tạo phòng:
  - Hiện mã PIN lớn
  - Danh sách: chủ phòng + người tham gia
  - Nút Moi ban be (copy PIN vào clipboard)
  - Nút Thoat phong (xoá phòng)
  - Nút Bat dau (chỉ host bấm được, cần đủ 2 người)
"""

import pygame
import os
import sys
import time
import random

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_ACCENT_HOV,
    C_TEXT, C_TEXT_DIM, C_OVERLAY, C_SUCCESS, C_ERROR,
    Button,
)

# import room registry từ ModalOpPvp
from ModalOpPvp import _ROOMS, close_room, join_room

C_HOST_COLOR   = (255, 215,  80)   # vàng — chủ phòng
C_GUEST_COLOR  = (100, 200, 255)   # xanh — khách
C_START_BG     = ( 50, 160, 100)
C_START_HOV    = ( 70, 200, 130)
C_START_DIS    = ( 40,  60,  40)   # disabled
C_LEAVE_BG     = (160,  50,  50)
C_LEAVE_HOV    = (200,  70,  70)
C_INVITE_BG    = ( 70,  70, 130)
C_INVITE_HOV   = (100, 100, 180)


class CreateMatch:
    W, H = 480, 460

    def __init__(self, screen_w, screen_h, pin: str, host: str, username: str,
                 display_name: str = ''):
        """
        pin          : mã PIN phòng đã tạo
        host         : username chủ phòng (dùng để so sánh is_host)
        username     : username người dùng hiện tại
        display_name : tên hiển thị (ưu tiên dùng thay username)
        """
        self.screen_w     = screen_w
        self.screen_h     = screen_h
        self.pin          = pin
        self.host         = host
        self.username     = username
        self.display_name = display_name or username   # fallback về username nếu chưa set
        self.is_host      = (username == host)

        self._result      = ...   # None | 'start' | 'leave'
        self._open_t      = 0
        self._msg         = ''
        self._msg_ok      = False
        self._msg_timer   = 0
        self._copied      = False

        self._init_fonts()
        self._build()

        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

        # đăng ký mình vào phòng nếu là guest
        if not self.is_host and pin in _ROOMS:
            _ROOMS[pin]['players'] = 2
            _ROOMS[pin]['guest']   = username

    # ── fonts ─────────────────────────────────────────────────────────────────

    def _init_fonts(self):
        self.f_title  = pygame.font.SysFont('segoeui', 18, bold=True)
        self.f_pin    = pygame.font.SysFont('segoeui', 48, bold=True)
        self.f_label  = pygame.font.SysFont('segoeui', 13)
        self.f_player = pygame.font.SysFont('segoeui', 15, bold=True)
        self.f_btn    = pygame.font.SysFont('segoeui', 14, bold=True)
        self.f_small  = pygame.font.SysFont('segoeui', 11)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)

        pad = 28
        iw  = self.W - pad * 2

        self.btn_close = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)

        # nút mời bạn bè
        self.btn_invite = Button(
            mx + pad, my + 230, iw, 40,
            text='📋  Sao chep ma PIN',
            bg=C_INVITE_BG, bg_hover=C_INVITE_HOV,
            text_color=C_TEXT, radius=10)

        # nút bắt đầu (chỉ host)
        self.btn_start = Button(
            mx + pad, my + 284, iw, 44,
            text='▶  Bat dau tran',
            bg=C_START_BG, bg_hover=C_START_HOV,
            text_color=(255, 255, 255), radius=12)

        # nút thoát phòng
        self.btn_leave = Button(
            mx + pad, my + 344, iw, 40,
            text='✕  Thoat phong',
            bg=C_LEAVE_BG, bg_hover=C_LEAVE_HOV,
            text_color=(255, 255, 255), radius=10)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_room(self) -> dict | None:
        return _ROOMS.get(self.pin)

    def _player_count(self) -> int:
        r = self._get_room()
        return r['players'] if r else 0

    def _guest_name(self) -> str:
        r = self._get_room()
        if r:
            return r.get('guest', '')
        return ''

    # ── run ───────────────────────────────────────────────────────────────────

    def run(self, surface) -> str | None:
        """Trả về 'start' | 'leave' | None"""
        self._result = ...
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()

        while self._result is ...:
            # kiểm tra phòng còn tồn tại không
            if self._get_room() is None and self.is_host is False:
                # host đã đóng phòng
                self._result = 'leave'
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._leave()
                    break
                self._handle(event)

            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)

        return self._result

    # ── events ────────────────────────────────────────────────────────────────

    def _handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._leave()
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_close.collidepoint(event.pos):
                self._leave()
                return
            if not self.panel_rect.collidepoint(event.pos):
                return

        if self.btn_invite.handle_event(event):
            self._copy_pin()

        if self.btn_leave.handle_event(event):
            self._leave()

        if self.btn_start.handle_event(event):
            if self.is_host and self._player_count() >= 2:
                self._result = 'start'
            elif self.is_host:
                self._msg     = 'Can 2 nguoi choi de bat dau!'
                self._msg_ok  = False
                self._msg_timer = pygame.time.get_ticks() + 2500

    def _copy_pin(self):
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(self.pin)
            root.update()
            root.destroy()
            self._msg     = f'Da sao chep: {self.pin}'
            self._msg_ok  = True
        except Exception:
            self._msg     = f'Ma PIN: {self.pin}'
            self._msg_ok  = True
        self._msg_timer = pygame.time.get_ticks() + 2500

    def _leave(self):
        if self.is_host:
            close_room(self.pin)
        elif self.pin in _ROOMS:
            _ROOMS[self.pin]['players'] = 1
            _ROOMS[self.pin].pop('guest', None)
        self._result = 'leave'

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

        # shadow
        sh = pygame.Surface((self.W + 20, self.H + 20), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 80))
        surface.blit(sh, (ox - 10, oy + 10))

        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)
        pygame.draw.rect(surface, C_ACCENT,
                         pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        # tiêu đề
        title = self.f_title.render('Phong cho', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox + self.W // 2, y=oy + 14))

        # nút đóng
        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        pad = 28

        # ── PIN lớn ──
        pin_lbl = self.f_pin.render(self.pin, True, C_HOST_COLOR)
        surface.blit(pin_lbl, pin_lbl.get_rect(centerx=ox + self.W // 2, y=oy + 44))

        hint = self.f_small.render('Ma PIN phong — chia se cho ban be', True, C_TEXT_DIM)
        surface.blit(hint, hint.get_rect(centerx=ox + self.W // 2, y=oy + 104))

        # ── divider ──
        pygame.draw.line(surface, C_BORDER,
                         (ox + pad, oy + 122), (ox + self.W - pad, oy + 122), 1)

        # ── danh sách người chơi ──
        player_y = oy + 132
        count = self._player_count()

        # host
        host_bg = pygame.Rect(ox + pad, player_y, self.W - pad * 2, 36)
        pygame.draw.rect(surface, C_PANEL2, host_bg, border_radius=8)
        crown = self.f_player.render('👑', True, C_HOST_COLOR)
        surface.blit(crown, (host_bg.x + 10, host_bg.centery - crown.get_height() // 2))
        # hiện display_name của host (lấy từ _ROOMS nếu có, fallback về self.host)
        room = self._get_room()
        host_display = room.get('host_display', self.host) if room else self.host
        host_lbl = self.f_player.render(host_display, True, C_HOST_COLOR)
        surface.blit(host_lbl, (host_bg.x + 38, host_bg.centery - host_lbl.get_height() // 2))
        role_lbl = self.f_small.render('Chu phong', True, C_TEXT_DIM)
        surface.blit(role_lbl, (host_bg.right - role_lbl.get_width() - 10,
                                host_bg.centery - role_lbl.get_height() // 2))

        # guest
        guest_y  = player_y + 44
        guest_bg = pygame.Rect(ox + pad, guest_y, self.W - pad * 2, 36)
        pygame.draw.rect(surface, C_PANEL2, guest_bg, border_radius=8)

        guest = self._guest_name()
        if guest:
            g_lbl = self.f_player.render('👤', True, C_GUEST_COLOR)
            surface.blit(g_lbl, (guest_bg.x + 10, guest_bg.centery - g_lbl.get_height() // 2))
            # ưu tiên guest_display nếu có
            room = self._get_room()
            guest_display = room.get('guest_display', guest) if room else guest
            gn_lbl = self.f_player.render(guest_display, True, C_GUEST_COLOR)
            surface.blit(gn_lbl, (guest_bg.x + 38, guest_bg.centery - gn_lbl.get_height() // 2))
            gr_lbl = self.f_small.render('Nguoi tham gia', True, C_TEXT_DIM)
            surface.blit(gr_lbl, (guest_bg.right - gr_lbl.get_width() - 10,
                                  guest_bg.centery - gr_lbl.get_height() // 2))
        else:
            # chờ người vào
            t    = pygame.time.get_ticks() / 600.0
            dots = '.' * (int(t) % 4)
            wait = self.f_label.render(f'Dang cho nguoi choi{dots}', True, C_TEXT_DIM)
            surface.blit(wait, wait.get_rect(center=guest_bg.center))
            # pulse border
            import math
            alpha = int(100 + 80 * math.sin(t * 2))
            pulse = pygame.Surface((guest_bg.w, guest_bg.h), pygame.SRCALPHA)
            pygame.draw.rect(pulse, (*C_ACCENT, alpha),
                             pulse.get_rect(), 2, border_radius=8)
            surface.blit(pulse, guest_bg.topleft)

        # ── nút mời ──
        orig = self.btn_invite.rect.copy()
        self.btn_invite.rect = self.btn_invite.rect.move(dx, dy)
        self.btn_invite.draw(surface, self.f_btn)
        self.btn_invite.rect = orig

        # ── nút bắt đầu ──
        can_start = self.is_host and count >= 2
        orig = self.btn_start.rect.copy()
        self.btn_start.rect = self.btn_start.rect.move(dx, dy)
        if can_start:
            self.btn_start.bg = C_START_BG
        else:
            self.btn_start.bg = C_START_DIS
        self.btn_start.draw(surface, self.f_btn)
        self.btn_start.rect = orig

        if not self.is_host:
            wait2 = self.f_small.render('Cho chu phong bat dau...', True, C_TEXT_DIM)
            surface.blit(wait2, wait2.get_rect(
                centerx=ox + self.W // 2,
                y=self.btn_start.rect.move(dx, dy).centery - wait2.get_height() // 2))

        # ── nút thoát ──
        orig = self.btn_leave.rect.copy()
        self.btn_leave.rect = self.btn_leave.rect.move(dx, dy)
        self.btn_leave.draw(surface, self.f_btn)
        self.btn_leave.rect = orig

        # ── thông báo ──
        if self._msg and pygame.time.get_ticks() < self._msg_timer:
            c  = C_SUCCESS if self._msg_ok else C_ERROR
            ml = self.f_label.render(self._msg, True, c)
            surface.blit(ml, ml.get_rect(
                centerx=ox + self.W // 2,
                y=self.btn_leave.rect.move(dx, dy).bottom + 8))
