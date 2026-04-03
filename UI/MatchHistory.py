"""
UI/MatchHistory.py
Component hiển thị lịch sử trận đấu dạng danh sách cuộn.
Dùng trong UserModal tab 'Lich su'.
"""

import pygame
import os, sys

_HERE   = os.path.dirname(os.path.abspath(__file__))
_ONLINE = os.path.join(os.path.dirname(_HERE), 'Online')
for _p in (_HERE, _ONLINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Colors ────────────────────────────────────────────────────────────────────
C_BG        = (18,  18,  30)
C_ROW_A     = (24,  24,  40)
C_ROW_B     = (28,  28,  46)
C_ROW_HOV   = (38,  50,  80)
C_BORDER    = (45,  45,  70)
C_TEXT      = (220, 220, 240)
C_DIM       = (110, 110, 145)
C_WIN       = ( 72, 199, 142)   # xanh lá
C_LOSS      = (220,  80,  80)   # đỏ
C_DRAW      = (150, 150, 200)   # xanh nhạt
C_WHITE_SQ  = (240, 235, 215)
C_BLACK_SQ  = ( 50,  50,  60)


def _result_color(result):
    return C_WIN if result == 'win' else (C_LOSS if result == 'loss' else C_DRAW)

def _result_symbol(result):
    return '+' if result == 'win' else ('-' if result == 'loss' else '=')


class MatchHistoryPanel:
    """
    Panel lịch sử trận đấu có thể cuộn.
    Dùng:
        panel = MatchHistoryPanel(x, y, width, height, user_id)
        panel.draw(surface)
        panel.handle_event(event)
    """

    ROW_H = 56

    def __init__(self, x, y, w, h, user_id: int, username: str = ''):
        self.rect     = pygame.Rect(x, y, w, h)
        self.user_id  = user_id
        self.username = username
        self._history = []
        self._scroll  = 0       # pixel offset
        self._loaded  = False

        self._init_fonts()

    def _init_fonts(self):
        self.f_name   = pygame.font.SysFont('segoeui', 14, bold=True)
        self.f_sub    = pygame.font.SysFont('segoeui', 12)
        self.f_result = pygame.font.SysFont('segoeui', 18, bold=True)
        self.f_sym    = pygame.font.SysFont('segoeui', 16, bold=True)
        self.f_date   = pygame.font.SysFont('segoeui', 12)
        self.f_empty  = pygame.font.SysFont('segoeui', 13)

    def load(self, limit=50):
        """Tải lịch sử từ database."""
        try:
            import DataSeverConfig as db
            self._history = db.get_match_history(self.user_id, limit)
        except Exception:
            self._history = []
        self._loaded = True
        self._scroll = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self._scroll -= event.y * 30
                self._clamp_scroll()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:   # scroll up
                self._scroll -= 30; self._clamp_scroll()
            elif event.button == 5: # scroll down
                self._scroll += 30; self._clamp_scroll()

    def _clamp_scroll(self):
        total = len(self._history) * self.ROW_H
        max_s = max(0, total - self.rect.h)
        self._scroll = max(0, min(self._scroll, max_s))

    def draw(self, surface):
        if not self._loaded:
            self.load()

        old_clip = surface.get_clip()
        surface.set_clip(self.rect)

        # nền
        pygame.draw.rect(surface, C_BG, self.rect)

        if not self._history:
            lbl = self.f_empty.render('Chua co lich su van dau.', True, C_DIM)
            surface.blit(lbl, lbl.get_rect(
                centerx=self.rect.centerx,
                centery=self.rect.y + 30))
            surface.set_clip(old_clip)
            return

        mouse = pygame.mouse.get_pos()
        for i, m in enumerate(self._history):
            ry = self.rect.y + i * self.ROW_H - self._scroll
            if ry + self.ROW_H < self.rect.y:
                continue
            if ry > self.rect.bottom:
                break

            row = pygame.Rect(self.rect.x, ry, self.rect.w, self.ROW_H - 1)
            bg  = C_ROW_HOV if row.collidepoint(mouse) else (C_ROW_A if i%2==0 else C_ROW_B)
            pygame.draw.rect(surface, bg, row)
            pygame.draw.line(surface, C_BORDER,
                             (self.rect.x, ry + self.ROW_H - 1),
                             (self.rect.right, ry + self.ROW_H - 1), 1)

            self._draw_row(surface, row, m)

        # scrollbar
        total = len(self._history) * self.ROW_H
        if total > self.rect.h:
            sb_h   = max(20, int(self.rect.h * self.rect.h / total))
            sb_y   = self.rect.y + int(self._scroll * (self.rect.h - sb_h) / (total - self.rect.h))
            sb_r   = pygame.Rect(self.rect.right - 4, sb_y, 4, sb_h)
            pygame.draw.rect(surface, (80, 80, 120), sb_r, border_radius=2)

        surface.set_clip(old_clip)

    def _draw_row(self, surface, row, m):
        x  = row.x + 10
        cy = row.centery
        result  = m.get('result', '')
        color   = m.get('color', 'white')
        opp     = m.get('opponent', '?')
        moves   = m.get('moves', 0)
        date_s  = str(m.get('played_at', ''))[:10]

        # ── icon màu quân ──
        sq_c = C_WHITE_SQ if color == 'white' else C_BLACK_SQ
        pygame.draw.rect(surface, sq_c, (x, cy - 8, 14, 14), border_radius=2)
        pygame.draw.rect(surface, C_BORDER, (x, cy - 8, 14, 14), 1, border_radius=2)
        x += 22

        # ── tên người chơi vs đối thủ ──
        me_lbl  = self.f_name.render(self.username or 'Ban', True, C_TEXT)
        opp_lbl = self.f_sub.render(f'vs  {opp}', True, C_DIM)
        surface.blit(me_lbl,  (x, cy - 14))
        surface.blit(opp_lbl, (x, cy + 2))
        x += 180

        # ── số nước đi ──
        mv_lbl = self.f_sub.render(f'{moves} nuoc', True, C_DIM)
        surface.blit(mv_lbl, mv_lbl.get_rect(centerx=x + 30, centery=cy))
        x += 80

        # ── ký hiệu kết quả ──
        sym   = _result_symbol(result)
        sym_c = _result_color(result)
        sym_s = self.f_sym.render(sym, True, (255, 255, 255))
        sym_bg = pygame.Rect(x, cy - 12, 24, 24)
        pygame.draw.rect(surface, sym_c, sym_bg, border_radius=6)
        surface.blit(sym_s, sym_s.get_rect(center=sym_bg.center))
        x += 40

        # ── kết quả text ──
        res_text = 'Thang' if result == 'win' else ('Thua' if result == 'loss' else 'Hoa')
        res_lbl  = self.f_name.render(res_text, True, sym_c)
        surface.blit(res_lbl, res_lbl.get_rect(centerx=x + 25, centery=cy))
        x += 70

        # ── ngày ──
        date_lbl = self.f_date.render(date_s, True, C_DIM)
        surface.blit(date_lbl, date_lbl.get_rect(
            right=row.right - 12, centery=cy))
