"""
UI/OutMenu.py
Modal xác nhận thoát ứng dụng từ menu.
Trả về: 'quit' | 'cancel'
"""

import pygame
import os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT,
    C_TEXT, C_TEXT_DIM, C_OVERLAY, C_ERROR, Button,
)

C_CANCEL_BG  = (50,  50,  80)
C_CANCEL_HOV = (70,  70, 110)
C_QUIT_BG    = (160, 50,  50)
C_QUIT_HOV   = (200, 70,  70)


class OutMenu:
    W, H = 400, 180

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._result  = ...
        self._open_t  = 0

        self._init_fonts()
        self._build()
        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 160))

    def _init_fonts(self):
        self.f_title = pygame.font.SysFont('segoeui', 18, bold=True)
        self.f_sub   = pygame.font.SysFont('segoeui', 13)
        self.f_btn   = pygame.font.SysFont('segoeui', 15, bold=True)

    def _build(self):
        mx  = self.screen_w // 2 - self.W // 2
        my  = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)
        pad = 28
        btn_w = (self.W - pad * 2 - 12) // 2
        btn_y = my + self.H - 60

        # trái: Bỏ qua
        self.btn_cancel = Button(
            mx + pad, btn_y, btn_w, 42,
            text='Bo qua',
            bg=C_CANCEL_BG, bg_hover=C_CANCEL_HOV,
            text_color=(255, 255, 255), radius=10)

        # phải: Xác nhận
        self.btn_quit = Button(
            mx + pad + btn_w + 12, btn_y, btn_w, 42,
            text='Xac nhan',
            bg=C_QUIT_BG, bg_hover=C_QUIT_HOV,
            text_color=(255, 255, 255), radius=10)

    def run(self, surface) -> str:
        """Trả về 'quit' hoặc 'cancel'."""
        self._result = ...
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()

        while self._result is ...:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._result = 'quit'
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._result = 'cancel'
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        self._result = 'quit'
                if self.btn_cancel.handle_event(event):
                    self._result = 'cancel'
                if self.btn_quit.handle_event(event):
                    self._result = 'quit'

            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)

        return self._result

    def _draw(self, surface):
        surface.blit(self._overlay, (0, 0))
        elapsed = (pygame.time.get_ticks() - self._open_t) / 180.0
        ease    = 1 - (1 - min(1.0, elapsed)) ** 3
        ox, oy  = self.panel_rect.x, self.panel_rect.y

        if ease < 1.0:
            old = surface.get_clip()
            sw = max(1, int(self.W * ease)); sh = max(1, int(self.H * ease))
            surface.set_clip(pygame.Rect(ox+(self.W-sw)//2, oy+(self.H-sh)//2, sw, sh))
        else:
            old = None

        pr = pygame.Rect(ox, oy, self.W, self.H)
        sh = pygame.Surface((self.W+20, self.H+20), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 70)); surface.blit(sh, (ox-10, oy+10))
        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)
        pygame.draw.rect(surface, C_ERROR, pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        title = self.f_title.render('Thoat ung dung?', True, C_TEXT)
        surface.blit(title, title.get_rect(centerx=ox+self.W//2, y=oy+20))

        sub = self.f_sub.render('Ban co chac muon thoat khong?', True, C_TEXT_DIM)
        surface.blit(sub, sub.get_rect(centerx=ox+self.W//2, y=oy+52))

        dx = ox - self.panel_rect.x; dy = oy - self.panel_rect.y
        for btn in (self.btn_cancel, self.btn_quit):
            orig = btn.rect.copy()
            btn.rect = btn.rect.move(dx, dy)
            btn.draw(surface, self.f_btn)
            btn.rect = orig

        if old is not None:
            surface.set_clip(old)
