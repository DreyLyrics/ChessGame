"""
UI/ModalChessColor.py
Modal chọn màu quân cờ trước khi bắt đầu ván.

Trả về: 'white' | 'black' | None (đóng modal)

Dùng:
    from ModalChessColor import ColorPickerModal
    modal = ColorPickerModal(screen_w, screen_h)
    color = modal.run(surface)   # blocking, trả về khi người dùng chọn
"""

import pygame
import random
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_TEXT, C_TEXT_DIM,
    C_OVERLAY, C_SUCCESS,
)

# ── màu sắc riêng ─────────────────────────────────────────────────────────────
C_WHITE_BG    = (240, 235, 220)
C_WHITE_HOV   = (255, 250, 240)
C_BLACK_BG    = (40,  40,  50)
C_BLACK_HOV   = (60,  60,  75)
C_RANDOM_BG   = (100, 80,  180)
C_RANDOM_HOV  = (130, 110, 210)
C_GOLD        = (255, 215, 80)


class ColorPickerModal:
    """
    Modal chọn màu quân cờ.
    Gọi .run(surface) để hiển thị, trả về 'white' | 'black' | None.
    """

    W, H = 480, 360

    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._result  = None          # 'white' | 'black' | None
        self._open_t  = 0

        self._init_fonts()
        self._build()

        # overlay mờ
        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 160))

        # icon quân vua (vẽ bằng pygame, không cần ảnh)
        self._anim_t = 0.0

    # ── fonts ─────────────────────────────────────────────────────────────────

    def _init_fonts(self):
        self.font_title  = pygame.font.SysFont('segoeui', 22, bold=True)
        self.font_sub    = pygame.font.SysFont('segoeui', 14)
        self.font_btn    = pygame.font.SysFont('segoeui', 17, bold=True)
        self.font_label  = pygame.font.SysFont('segoeui', 13)
        self.font_icon   = pygame.font.SysFont('segoeui', 36, bold=True)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)

        pad   = 32
        btn_w = (self.W - pad * 2 - 20) // 3   # 3 nút chia đều
        btn_h = 110
        by    = my + self.H - btn_h - pad

        self.btn_white = pygame.Rect(mx + pad,                    by, btn_w, btn_h)
        self.btn_black = pygame.Rect(mx + pad + btn_w + 10,       by, btn_w, btn_h)
        self.btn_rand  = pygame.Rect(mx + pad + (btn_w + 10) * 2, by, btn_w, btn_h)

        # nút đóng X
        self.btn_close = pygame.Rect(mx + self.W - 38, my + 12, 26, 26)

    # ── draw ──────────────────────────────────────────────────────────────────

    def _draw(self, surface):
        self._anim_t = pygame.time.get_ticks() / 1000.0

        # overlay
        surface.blit(self._overlay, (0, 0))

        # scale-in animation
        elapsed = (pygame.time.get_ticks() - self._open_t) / 200.0
        ease    = 1 - (1 - min(1.0, elapsed)) ** 3

        if ease < 1.0:
            sw  = max(1, int(self.W * ease))
            sh  = max(1, int(self.H * ease))
            tmp = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            self._draw_panel(tmp, 0, 0)
            scaled = pygame.transform.smoothscale(tmp, (sw, sh))
            surface.blit(scaled, (self.panel_rect.centerx - sw // 2,
                                  self.panel_rect.centery - sh // 2))
        else:
            self._draw_panel(surface, self.panel_rect.x, self.panel_rect.y)

    def _draw_panel(self, surface, ox, oy):
        pr = pygame.Rect(ox, oy, self.W, self.H)
        dx = ox - self.panel_rect.x
        dy = oy - self.panel_rect.y

        # shadow
        sh = pygame.Surface((self.W + 20, self.H + 20), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 70))
        surface.blit(sh, (ox - 10, oy + 10))

        # nền panel
        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)

        # thanh accent trên
        pygame.draw.rect(surface, C_ACCENT,
                         pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        # tiêu đề
        title = self.font_title.render('Chon mau quan co', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox + self.W // 2, y=oy + 18))

        # mô tả
        sub = self.font_sub.render('Ban muon choi quan mau nao?', True, C_TEXT_DIM)
        surface.blit(sub, sub.get_rect(centerx=ox + self.W // 2, y=oy + 50))

        # nút đóng X
        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.font_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        # 3 nút chọn màu
        mouse = pygame.mouse.get_pos()
        self._draw_color_btn(surface, self.btn_white.move(dx, dy),
                             'Trang', C_WHITE_BG, C_WHITE_HOV,
                             (20, 20, 20), '♔', mouse)
        self._draw_color_btn(surface, self.btn_black.move(dx, dy),
                             'Den', C_BLACK_BG, C_BLACK_HOV,
                             (220, 220, 220), '♚', mouse)
        self._draw_random_btn(surface, self.btn_rand.move(dx, dy), mouse)

    def _draw_color_btn(self, surface, rect, label, bg, bg_hov,
                        text_color, icon, mouse):
        hovered = rect.collidepoint(mouse)
        color   = bg_hov if hovered else bg

        pygame.draw.rect(surface, color, rect, border_radius=12)
        pygame.draw.rect(surface, C_BORDER, rect, 2, border_radius=12)

        # icon quân vua
        icon_lbl = self.font_icon.render(icon, True, text_color)
        surface.blit(icon_lbl, icon_lbl.get_rect(
            centerx=rect.centerx, y=rect.y + 14))

        # tên màu
        name_lbl = self.font_btn.render(label, True, text_color)
        surface.blit(name_lbl, name_lbl.get_rect(
            centerx=rect.centerx, y=rect.bottom - 30))

        # viền sáng khi hover
        if hovered:
            pygame.draw.rect(surface, C_GOLD, rect, 3, border_radius=12)

    def _draw_random_btn(self, surface, rect, mouse):
        hovered = rect.collidepoint(mouse)
        color   = C_RANDOM_HOV if hovered else C_RANDOM_BG

        pygame.draw.rect(surface, color, rect, border_radius=12)
        pygame.draw.rect(surface, C_BORDER, rect, 2, border_radius=12)

        # icon xúc xắc quay theo thời gian
        t     = self._anim_t
        angle = math.sin(t * 2) * 15   # lắc nhẹ ±15°
        dice  = self.font_icon.render('?', True, (255, 255, 255))
        rotated = pygame.transform.rotate(dice, angle)
        surface.blit(rotated, rotated.get_rect(
            centerx=rect.centerx, centery=rect.y + 44))

        name_lbl = self.font_btn.render('Ngau nhien', True, (255, 255, 255))
        surface.blit(name_lbl, name_lbl.get_rect(
            centerx=rect.centerx, y=rect.bottom - 30))

        if hovered:
            pygame.draw.rect(surface, C_GOLD, rect, 3, border_radius=12)

    # ── event ─────────────────────────────────────────────────────────────────

    def _handle_event(self, event):
        dx = 0
        dy = 0

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._result = None
            return True   # đóng

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            # nút đóng
            if self.btn_close.collidepoint(pos):
                self._result = None
                return True

            # click ngoài panel → đóng
            if not self.panel_rect.collidepoint(pos):
                self._result = None
                return True

            if self.btn_white.collidepoint(pos):
                self._result = 'white'
                return True

            if self.btn_black.collidepoint(pos):
                self._result = 'black'
                return True

            if self.btn_rand.collidepoint(pos):
                self._result = random.choice(['white', 'black'])
                return True

        return False

    # ── public API ────────────────────────────────────────────────────────────

    def run(self, surface) -> str:
        """
        Hiển thị modal, block cho đến khi người dùng chọn.
        Trả về 'white' | 'black' | None (nếu đóng).
        """
        self._result = ...   # sentinel — chưa chọn
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()

        while self._result is ...:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._result = None
                    break
                self._handle_event(event)

            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)

        return self._result   # 'white' | 'black' | None
