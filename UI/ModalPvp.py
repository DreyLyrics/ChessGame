"""
UI/ModalPvp.py
Modal chọn chế độ PVP Online:
  - Nút 1: Tim tran  — matchmaking tự động
  - Nút 2: Tuy chinh tran — vào ModalOpPvp (tạo/tìm phòng)
"""

import pygame
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_ACCENT_HOV,
    C_TEXT, C_TEXT_DIM, C_OVERLAY, C_SUCCESS, C_ERROR,
    Button,
)

C_MATCH_BG  = ( 60, 130, 220)
C_MATCH_HOV = ( 90, 160, 255)
C_ROOM_BG   = ( 80,  60, 180)
C_ROOM_HOV  = (110,  90, 220)


class ModalPvp:
    W, H = 420, 300

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._result  = ...   # None | 'matchmaking' | 'custom'
        self._open_t  = 0
        self._searching = False
        self._search_t  = 0

        self._init_fonts()
        self._build()

        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

    def _init_fonts(self):
        self.f_title = pygame.font.SysFont('segoeui', 20, bold=True)
        self.f_label = pygame.font.SysFont('segoeui', 13)
        self.f_btn   = pygame.font.SysFont('segoeui', 16, bold=True)
        self.f_sub   = pygame.font.SysFont('segoeui', 12)
        self.f_dots  = pygame.font.SysFont('segoeui', 22, bold=True)

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)

        pad = 32
        iw  = self.W - pad * 2

        self.btn_close = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)

        self.btn_match = Button(
            mx + pad, my + 80, iw, 60,
            text='🔍  Tim tran',
            bg=C_MATCH_BG, bg_hover=C_MATCH_HOV,
            text_color=(255, 255, 255), radius=14)

        self.btn_custom = Button(
            mx + pad, my + 168, iw, 60,
            text='🏠  Tuy chinh tran',
            bg=C_ROOM_BG, bg_hover=C_ROOM_HOV,
            text_color=(255, 255, 255), radius=14)

    def run(self, surface):
        self._result = ...
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        while self._result is ...:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._result = None
                    break
                self._handle(event)
            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)
        return self._result

    def _handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._result = None
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_close.collidepoint(event.pos):
                self._result = None
                return
            if not self.panel_rect.collidepoint(event.pos):
                self._result = None
                return
        if self.btn_match.handle_event(event):
            self._result = 'matchmaking'
        if self.btn_custom.handle_event(event):
            self._result = 'custom'

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

        title = self.f_title.render('PVP Online', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox + self.W // 2, y=oy + 16))

        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        # nút Tim tran
        orig = self.btn_match.rect.copy()
        self.btn_match.rect = self.btn_match.rect.move(dx, dy)
        self.btn_match.draw(surface, self.f_btn)
        self.btn_match.rect = orig
        sub1 = self.f_sub.render('Tu dong ghep doi voi nguoi choi ngau nhien', True, C_TEXT_DIM)
        surface.blit(sub1, sub1.get_rect(
            centerx=ox + self.W // 2,
            y=self.btn_match.rect.move(dx, dy).bottom + 5))

        # nút Tuy chinh tran
        orig = self.btn_custom.rect.copy()
        self.btn_custom.rect = self.btn_custom.rect.move(dx, dy)
        self.btn_custom.draw(surface, self.f_btn)
        self.btn_custom.rect = orig
        sub2 = self.f_sub.render('Tao phong hoac tim phong bang ma PIN', True, C_TEXT_DIM)
        surface.blit(sub2, sub2.get_rect(
            centerx=ox + self.W // 2,
            y=self.btn_custom.rect.move(dx, dy).bottom + 5))
