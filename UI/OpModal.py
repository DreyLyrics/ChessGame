"""
UI/OpModal.py  —  Modal tuỳ chỉnh cài đặt game
Chức năng:
  - Âm lượng (áp dụng ngay vào pygame.mixer)
  - Gợi ý nước đi (bật/tắt)
  - Theme bàn cờ (4 theme từ config.py)
  - Tốc độ animation
"""

import pygame
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_ACCENT_HOV,
    C_TEXT, C_TEXT_DIM, C_SUCCESS, C_OVERLAY,
    Button,
)

DEFAULT_SETTINGS = {
    'volume':     80,
    'show_hints': True,
    'theme':      0,
    'anim_speed': 1,
}

# Tên theme khớp với thứ tự trong config.py: green, brown, blue, gray
THEME_NAMES   = ['Green', 'Brown', 'Blue', 'Gray']
THEME_COLORS  = [
    ((234, 235, 200), (119, 154,  88)),   # green
    ((235, 209, 166), (165, 117,  80)),   # brown
    ((229, 228, 200), ( 60,  95, 135)),   # blue
    ((120, 119, 118), ( 86,  85,  84)),   # gray
]
ANIM_LABELS   = ['Cham', 'Binh thuong', 'Nhanh']


class OpModal:
    W, H = 500, 480

    def __init__(self, screen_w, screen_h, settings: dict = None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.settings = dict(DEFAULT_SETTINGS)
        if settings:
            self.settings.update(settings)

        self._result        = ...
        self._open_t        = 0
        self._msg           = ''
        self._dragging_vol  = False

        self._init_fonts()
        self._build()

        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

    # ── fonts ─────────────────────────────────────────────────────────────────

    def _init_fonts(self):
        self.f_title = pygame.font.SysFont('segoeui', 19, bold=True)
        self.f_label = pygame.font.SysFont('segoeui', 13)
        self.f_val   = pygame.font.SysFont('segoeui', 13, bold=True)
        self.f_btn   = pygame.font.SysFont('segoeui', 13, bold=True)
        self.f_small = pygame.font.SysFont('segoeui', 11)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        mx  = self.screen_w // 2 - self.W // 2
        my  = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)

        pad = 30
        iw  = self.W - pad * 2

        self.btn_close = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)

        # row y positions — đều nhau, mỗi section cách nhau 16px
        self._row_vol   = my + 58
        self._row_hint  = my + 120
        self._row_theme = my + 182
        self._row_anim  = my + 318

        # volume track — label bên trái, track chiếm phần còn lại
        label_w = 100
        self._vol_track = pygame.Rect(mx + pad + label_w, self._row_vol + 10,
                                      iw - label_w - 50, 6)

        # toggle hint
        self._hint_rect = pygame.Rect(mx + pad + label_w, self._row_hint + 6, 40, 22)

        # theme swatches — 4 cái, mỗi cái 52px, gap 12px, căn giữa
        sw = 52
        gap_sw = 12
        total_sw = len(THEME_NAMES) * sw + (len(THEME_NAMES) - 1) * gap_sw
        sw_start = mx + self.W // 2 - total_sw // 2
        self._theme_swatches = [
            pygame.Rect(sw_start + i * (sw + gap_sw), self._row_theme + 22, sw, 44)
            for i in range(len(THEME_NAMES))
        ]

        # anim speed buttons — 3 nút đều nhau
        aw = (iw - 16) // 3
        self._anim_btns = [
            pygame.Rect(mx + pad + i * (aw + 8), self._row_anim + 22, aw, 34)
            for i in range(3)
        ]

        # save button
        self.btn_save = Button(
            mx + pad, my + self.H - 56, iw, 40,
            text='Luu cai dat',
            bg=C_ACCENT, bg_hover=C_ACCENT_HOV,
            text_color=(10, 10, 20), radius=10)

    # ── run ───────────────────────────────────────────────────────────────────

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

    # ── events ────────────────────────────────────────────────────────────────

    def _handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._result = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.btn_close.collidepoint(pos):
                self._result = None
                return
            if not self.panel_rect.collidepoint(pos):
                self._result = None
                return

            # volume slider
            t = self._vol_track
            hit_area = pygame.Rect(t.x - 10, t.y - 12, t.w + 20, t.h + 24)
            if hit_area.collidepoint(pos):
                self._dragging_vol = True
                self._set_vol_from_x(pos[0])

            # toggle hints
            if self._hint_rect.collidepoint(pos):
                self.settings['show_hints'] = not self.settings['show_hints']

            # theme swatches
            for i, sr in enumerate(self._theme_swatches):
                if sr.collidepoint(pos):
                    self.settings['theme'] = i
                    self._apply_theme(i)

            # anim speed
            for i, r in enumerate(self._anim_btns):
                if r.collidepoint(pos):
                    self.settings['anim_speed'] = i

        if event.type == pygame.MOUSEMOTION and self._dragging_vol:
            self._set_vol_from_x(event.pos[0])

        if event.type == pygame.MOUSEBUTTONUP:
            self._dragging_vol = False

        if self.btn_save.handle_event(event):
            self._save()

    def _set_vol_from_x(self, x):
        t     = self._vol_track
        ratio = max(0.0, min(1.0, (x - t.x) / t.w))
        vol   = int(ratio * 100)
        self.settings['volume'] = vol
        # áp dụng ngay
        v = vol / 100.0
        try:
            pygame.mixer.music.set_volume(v)
        except Exception:
            pass
        try:
            # set volume cho tất cả Sound channel
            for ch in range(pygame.mixer.get_num_channels()):
                pygame.mixer.Channel(ch).set_volume(v)
        except Exception:
            pass

    def _apply_theme(self, idx):
        """Áp dụng theme vào game nếu đang chạy (thông qua global config nếu có)."""
        try:
            import sys as _sys
            _src = os.path.join(os.path.dirname(_HERE), 'src')
            if _src not in _sys.path:
                _sys.path.insert(0, _src)
            from config import Config
            # Không có instance game ở đây — chỉ lưu idx, game sẽ đọc khi khởi tạo
        except Exception:
            pass

    def _save(self):
        self._msg    = 'Da luu cai dat!'
        self._result = dict(self.settings)

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
        title = self.f_title.render('Tuy chinh', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox + self.W // 2, y=oy + 14))

        # nút đóng
        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        pad = 30

        # ── divider helper ──
        def divider(y):
            pygame.draw.line(surface, C_BORDER,
                             (ox + pad, y), (ox + self.W - pad, y), 1)

        # ── Volume ──────────────────────────────────────────────────────
        ry = oy + (self._row_vol - self.panel_rect.y)
        lbl = self.f_label.render('Am luong', True, C_TEXT_DIM)
        surface.blit(lbl, (ox + pad, ry + 6))

        track = self._vol_track.move(dx, dy)
        # track bg
        pygame.draw.rect(surface, C_PANEL2,
                         pygame.Rect(track.x, track.centery - 3, track.w, 6),
                         border_radius=3)
        # fill
        fill_w = int(track.w * self.settings['volume'] / 100)
        if fill_w > 0:
            pygame.draw.rect(surface, C_ACCENT,
                             pygame.Rect(track.x, track.centery - 3, fill_w, 6),
                             border_radius=3)
        # thumb
        tx = track.x + fill_w
        pygame.draw.circle(surface, (255, 255, 255), (tx, track.centery), 10)
        pygame.draw.circle(surface, C_ACCENT,        (tx, track.centery), 10, 2)
        pygame.draw.circle(surface, C_ACCENT,        (tx, track.centery), 4)

        vol_lbl = self.f_val.render(f'{self.settings["volume"]}%', True, C_TEXT)
        surface.blit(vol_lbl, (track.right + 10,
                               track.centery - vol_lbl.get_height() // 2))

        divider(ry + 36)

        # ── Gợi ý nước đi ───────────────────────────────────────────────
        ry2 = oy + (self._row_hint - self.panel_rect.y)
        lbl2 = self.f_label.render('Goi y nuoc di', True, C_TEXT_DIM)
        surface.blit(lbl2, (ox + pad, ry2 + 7))

        hr = self._hint_rect.move(dx, dy)
        on = self.settings['show_hints']
        bg_toggle = C_ACCENT if on else C_PANEL2
        pygame.draw.rect(surface, bg_toggle, hr, border_radius=11)
        pygame.draw.rect(surface, C_BORDER,  hr, 1, border_radius=11)
        cx_t = hr.x + hr.w - 11 if on else hr.x + 11
        pygame.draw.circle(surface, (255, 255, 255), (cx_t, hr.centery), 9)

        state_lbl = self.f_small.render('Bat' if on else 'Tat', True,
                                        C_ACCENT if on else C_TEXT_DIM)
        surface.blit(state_lbl, (hr.right + 8, hr.centery - state_lbl.get_height() // 2))

        divider(ry2 + 36)

        # ── Theme bàn cờ ────────────────────────────────────────────────
        ry3 = oy + (self._row_theme - self.panel_rect.y)
        lbl3 = self.f_label.render('Theme ban co', True, C_TEXT_DIM)
        surface.blit(lbl3, (ox + pad, ry3 + 4))

        for i, sr in enumerate(self._theme_swatches):
            r = sr.move(dx, dy)
            light, dark = THEME_COLORS[i]
            pygame.draw.rect(surface, light,
                             pygame.Rect(r.x, r.y, r.w // 2, r.h), border_radius=6)
            pygame.draw.rect(surface, dark,
                             pygame.Rect(r.x + r.w // 2, r.y, r.w - r.w // 2, r.h),
                             border_radius=6)
            sel = (self.settings['theme'] == i)
            border_c = (255, 255, 255) if sel else C_BORDER
            border_w = 2 if sel else 1
            pygame.draw.rect(surface, border_c, r, border_w, border_radius=6)

            name = self.f_small.render(THEME_NAMES[i], True,
                                       C_TEXT if sel else C_TEXT_DIM)
            surface.blit(name, name.get_rect(centerx=r.centerx, y=r.bottom + 5))

        divider(ry3 + 90)

        # ── Tốc độ animation ────────────────────────────────────────────
        ry4 = oy + (self._row_anim - self.panel_rect.y)
        lbl4 = self.f_label.render('Toc do animation', True, C_TEXT_DIM)
        surface.blit(lbl4, (ox + pad, ry4 + 4))

        for i, r in enumerate(self._anim_btns):
            r2  = r.move(dx, dy)
            act = (self.settings['anim_speed'] == i)
            bg  = C_ACCENT if act else C_PANEL2
            tc  = (10, 10, 20) if act else C_TEXT_DIM
            pygame.draw.rect(surface, bg, r2, border_radius=8)
            pygame.draw.rect(surface, C_BORDER, r2, 1, border_radius=8)
            lbl = self.f_btn.render(ANIM_LABELS[i], True, tc)
            surface.blit(lbl, lbl.get_rect(center=r2.center))

        # ── nút lưu ─────────────────────────────────────────────────────
        orig = self.btn_save.rect.copy()
        self.btn_save.rect = self.btn_save.rect.move(dx, dy)
        self.btn_save.draw(surface, self.f_btn)
        self.btn_save.rect = orig
