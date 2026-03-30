"""
src/tracking.py
Chứa 2 component UI tách biệt:
  - TurnPanel  : thanh lượt chơi phía dưới bàn cờ
  - Sidebar    : panel bên phải (quân bị ăn + lịch sử nước đi)
Được dùng bởi Game thông qua composition.
"""

import pygame
from collections import Counter

from const import *

# ------------------------------------------------------------------ #
#  COLORS                                                              #
# ------------------------------------------------------------------ #
COLOR_PANEL_WHITE = (240, 217, 181)
COLOR_PANEL_BLACK = (40,  40,  40)
COLOR_TEXT_LIGHT  = (255, 255, 255)
COLOR_TEXT_DARK   = (20,  20,  20)
COLOR_CHECK       = (220, 50,  50)

SB_BG        = (22,  22,  35)
SB_HEADER_W  = (60,  100, 180)
SB_HEADER_B  = (35,  35,  55)
SB_ROW_EVEN  = (28,  28,  44)
SB_ROW_ODD   = (24,  24,  38)
SB_ACCENT    = (100, 160, 255)
SB_TEXT_DIM  = (110, 110, 140)
SB_ACTIVE_BG = (50,  80,  140)

PIECE_ORDER = ['queen', 'rook', 'bishop', 'knight', 'pawn']


# ------------------------------------------------------------------ #
#  TURN PANEL                                                          #
# ------------------------------------------------------------------ #

class TurnPanel:
    """Thanh hiển thị lượt chơi phía dưới bàn cờ."""

    def __init__(self):
        self._font_turn = pygame.font.SysFont('monospace', 20, bold=True)
        self._font_hint = pygame.font.SysFont('monospace', 13)

    def draw(self, surface, next_player: str, in_check: bool, move_count: int):
        px = BOARD_OFFSET_X
        py = PANEL_Y
        bg = COLOR_PANEL_WHITE if next_player == 'white' else COLOR_PANEL_BLACK
        pygame.draw.rect(surface, bg, (px, py, BOARD_W, PANEL_HEIGHT))

        # chỉ báo màu quân
        ind_color = (255, 255, 255) if next_player == 'white' else (20, 20, 20)
        cx, cy = px + 26, py + PANEL_HEIGHT // 2
        pygame.draw.circle(surface, ind_color,     (cx, cy), 13)
        pygame.draw.circle(surface, (100,100,100), (cx, cy), 13, 2)

        player_name = 'Trang' if next_player == 'white' else 'Den'
        text_color  = COLOR_TEXT_DARK if next_player == 'white' else COLOR_TEXT_LIGHT

        if in_check:
            lbl = self._font_turn.render(
                f'Luot {move_count+1}: {player_name}  !! CHIEU !!', True, COLOR_CHECK)
        else:
            lbl = self._font_turn.render(
                f'Luot {move_count+1}: {player_name}', True, text_color)
        surface.blit(lbl, (px + 48, cy - lbl.get_height() // 2))

        hint_color = (130,130,130) if next_player == 'white' else (100,100,100)
        hint = self._font_hint.render('T:theme  R:reset  M:menu', True, hint_color)
        surface.blit(hint, (px + BOARD_W - hint.get_width() - 8,
                             cy - hint.get_height() // 2))


# ------------------------------------------------------------------ #
#  SIDEBAR                                                             #
# ------------------------------------------------------------------ #

class Sidebar:
    """Panel bên phải: header lượt, quân bị ăn, lịch sử nước đi."""

    ICON_CAP  = 24   # icon quân bị ăn
    ICON_LOG  = 16   # icon trong move log
    CAP_H     = 110  # chiều cao cố định phần captured

    def __init__(self, img_loader):
        """
        img_loader: callable(path) -> pygame.Surface
                    (dùng chung cache ảnh với Game)
        """
        self._load = img_loader
        self._font_hdr = pygame.font.SysFont('segoeui', 14, bold=True)
        self._font_sb  = pygame.font.SysFont('segoeui', 13)
        self._font_sm  = pygame.font.SysFont('segoeui', 11)

    # ---------------------------------------------------------------- #

    def draw(self, surface, next_player: str, in_check: bool,
             move_log: list, captured: dict, move_count: int):
        sx = SIDEBAR_X
        sw = SIDEBAR_W

        # nền toàn sidebar
        pygame.draw.rect(surface, SB_BG, (sx, 0, sw, HEIGHT))
        pygame.draw.line(surface, (50, 50, 75), (sx, 0), (sx, HEIGHT), 2)

        y = 8
        y = self._draw_header(surface, sx, sw, y, next_player, in_check, move_count)
        y = self._draw_captured(surface, sx, sw, y, captured)
        self._draw_move_log(surface, sx, sw, y, move_log)

    # ---------------------------------------------------------------- #
    #  HEADER                                                            #
    # ---------------------------------------------------------------- #

    def _draw_header(self, surface, sx, sw, y,
                     next_player, in_check, move_count):
        hdr_bg   = SB_HEADER_W if next_player == 'white' else SB_HEADER_B
        hdr_rect = pygame.Rect(sx+6, y, sw-12, 44)
        pygame.draw.rect(surface, hdr_bg, hdr_rect, border_radius=8)

        ind_c = (255,255,255) if next_player == 'white' else (20,20,20)
        pygame.draw.circle(surface, ind_c,         (sx+22, y+22), 11)
        pygame.draw.circle(surface, (150,150,150), (sx+22, y+22), 11, 2)

        pname = 'Trang' if next_player == 'white' else 'Den'
        tc    = COLOR_TEXT_DARK if next_player == 'white' else COLOR_TEXT_LIGHT
        if in_check:
            htxt = self._font_hdr.render(f'{pname} - !! CHIEU !!', True, COLOR_CHECK)
        else:
            htxt = self._font_hdr.render(f'Luot cua: {pname}', True, tc)
        surface.blit(htxt, (sx+38, y + 22 - htxt.get_height()//2))

        mn_color = (180,180,180) if next_player == 'white' else (130,130,160)
        mn = self._font_sm.render(f'Nuoc thu {move_count+1}', True, mn_color)
        surface.blit(mn, (hdr_rect.right - mn.get_width() - 6,
                          y + 22 - mn.get_height()//2))
        return y + 52

    # ---------------------------------------------------------------- #
    #  QUÂN BỊ ĂN                                                       #
    # ---------------------------------------------------------------- #

    def _draw_captured(self, surface, sx, sw, y, captured):
        ICON = self.ICON_CAP
        for color, label in [('white', 'Trang an duoc:'), ('black', 'Den an duoc:')]:
            lbl = self._font_hdr.render(label, True, SB_ACCENT)
            surface.blit(lbl, (sx+8, y))
            y += lbl.get_height() + 4

            pieces = captured[color]
            if not pieces:
                empty = self._font_sb.render('(chua an duoc quan nao)', True, SB_TEXT_DIM)
                surface.blit(empty, (sx+10, y))
                y += empty.get_height() + 10
                continue

            enemy = 'black' if color == 'white' else 'white'
            counts = Counter(pieces)
            ix = sx + 8
            for name in PIECE_ORDER:
                cnt = counts.get(name, 0)
                if not cnt:
                    continue
                img  = self._load(f'assets/images/imgs-80px/{enemy}_{name}.png')
                icon = pygame.transform.smoothscale(img, (ICON, ICON))
                for _ in range(cnt):
                    if ix + ICON > sx + sw - 6:
                        ix  = sx + 8
                        y  += ICON + 2
                    surface.blit(icon, (ix, y))
                    ix += ICON + 2
            y += ICON + 10
        return y

    # ---------------------------------------------------------------- #
    #  LỊCH SỬ NƯỚC ĐI                                                  #
    # ---------------------------------------------------------------- #

    def _draw_move_log(self, surface, sx, sw, y_start, log):
        if not log:
            lbl = self._font_sb.render('Chua co nuoc di nao.', True, SB_TEXT_DIM)
            surface.blit(lbl, (sx+8, y_start))
            return

        hdr = self._font_hdr.render('Lich su nuoc di:', True, SB_ACCENT)
        surface.blit(hdr, (sx+8, y_start))
        y_start += hdr.get_height() + 4

        col_w  = (sw - 16) // 2
        wh_h   = self._font_sm.render('Trang', True, (200,200,220))
        bl_h   = self._font_sm.render('Den',   True, (160,160,190))
        surface.blit(wh_h, (sx+8,         y_start))
        surface.blit(bl_h, (sx+8+col_w,   y_start))
        pygame.draw.line(surface, (50,50,75),
                         (sx+6,    y_start + wh_h.get_height() + 1),
                         (sx+sw-6, y_start + wh_h.get_height() + 1), 1)
        y_start += wh_h.get_height() + 4

        ICON      = self.ICON_LOG
        row_h     = ICON + 6
        visible_h = HEIGHT - y_start - 8
        max_rows  = visible_h // row_h

        # ghép cặp
        pairs, i = [], 0
        while i < len(log):
            we = log[i] if log[i][1] == 'white' else None
            be = log[i+1] if (i+1 < len(log) and log[i+1][1] == 'black') else None
            if we is None:
                be = log[i]
            pairs.append((we, be))
            i += 2 if (we and be) else 1

        start = max(0, len(pairs) - max_rows)
        visible = pairs[start:]

        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(sx, y_start, sw, visible_h))

        for idx, (we, be) in enumerate(visible):
            row_y   = y_start + idx * row_h
            pair_n  = start + idx + 1
            is_last = (idx == len(visible) - 1)

            bg = SB_ACTIVE_BG if is_last else (SB_ROW_EVEN if idx%2==0 else SB_ROW_ODD)
            pygame.draw.rect(surface, bg, (sx+4, row_y, sw-8, row_h-1))

            num = self._font_sm.render(f'{pair_n}.', True, SB_TEXT_DIM)
            surface.blit(num, (sx+5, row_y + row_h//2 - num.get_height()//2))

            self._draw_entry(surface, we, sx+20,          row_y, row_h, ICON, is_last)
            self._draw_entry(surface, be, sx+8+col_w+14,  row_y, row_h, ICON, is_last)

        surface.set_clip(old_clip)

    def _draw_entry(self, surface, entry, col_x, row_y, row_h, ICON, is_last):
        if entry is None:
            return
        name, color, frm, to, cap = entry

        img  = self._load(f'assets/images/imgs-80px/{color}_{name}.png')
        icon = pygame.transform.smoothscale(img, (ICON, ICON))
        iy   = row_y + row_h//2 - ICON//2
        surface.blit(icon, (col_x, iy))

        tc  = (255,255,180) if is_last else (210,210,235)
        lbl = self._font_sm.render(f'{frm}-{to}', True, tc)
        surface.blit(lbl, (col_x + ICON + 3, row_y + row_h//2 - lbl.get_height()//2))

        if cap:
            cap_color = 'black' if color == 'white' else 'white'
            ci   = self._load(f'assets/images/imgs-80px/{cap_color}_{cap}.png')
            cico = pygame.transform.smoothscale(ci, (ICON-2, ICON-2))
            xl   = self._font_sm.render('x', True, (220,80,80))
            xoff = col_x + ICON + 3 + lbl.get_width() + 2
            surface.blit(xl,   (xoff, row_y + row_h//2 - xl.get_height()//2))
            surface.blit(cico, (xoff + xl.get_width() + 1,
                                row_y + row_h//2 - (ICON-2)//2))
