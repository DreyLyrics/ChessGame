import pygame
import math

from const import *
from board import Board
from dragger import Dragger
from config import Config
from square import Square
from piece import King
from tracking import TurnPanel, Sidebar

# ------------------------------------------------------------------ #
#  COLORS                                                              #
# ------------------------------------------------------------------ #
COLOR_PANEL_WHITE = (240, 217, 181)
COLOR_PANEL_BLACK = (40,  40,  40)
COLOR_TEXT_LIGHT  = (255, 255, 255)
COLOR_TEXT_DARK   = (20,  20,  20)
COLOR_CHECK       = (220, 50,  50)
COLOR_STALEMATE   = (80,  80,  200)

# sidebar
SB_BG         = (22,  22,  35)
SB_HEADER_W   = (60,  100, 180)   # header Trắng
SB_HEADER_B   = (35,  35,  55)    # header Đen
SB_ROW_EVEN   = (28,  28,  44)
SB_ROW_ODD    = (24,  24,  38)
SB_ACCENT     = (100, 160, 255)
SB_CAPTURE    = (220, 80,  80)
SB_TEXT       = (210, 210, 230)
SB_TEXT_DIM   = (110, 110, 140)
SB_ACTIVE_BG  = (50,  80,  140)   # nền lượt đang đi

BOARD_H = SQSIZE * ROWS   # chiều cao vùng bàn cờ

# kết quả
RESULT_NONE      = 0
RESULT_CHECKMATE = 1
RESULT_STALEMATE = 2
RESULT_KING_DEAD = 3

# ký hiệu quân cờ
PIECE_SYM = {
    'king':   ('K', 'k'),   # (white, black)
    'queen':  ('Q', 'q'),
    'rook':   ('R', 'r'),
    'bishop': ('B', 'b'),
    'knight': ('N', 'n'),
    'pawn':   ('P', 'p'),
}


class Game:

    def __init__(self):
        self.next_player = 'white'
        self.hovered_sqr = None
        self.board       = Board()
        self.dragger     = Dragger()
        self.config      = Config()

        self.winner      = None
        self.game_result = RESULT_NONE
        self.in_check    = False

        self._alert_text  = ''
        self._alert_timer = 0
        self._alert_color = COLOR_CHECK
        self._ALERT_DUR   = 120

        self._img_cache: dict = {}

        # fonts
        self._font_coord  = pygame.font.SysFont('monospace', 16, bold=True)
        self._font_turn   = pygame.font.SysFont('monospace', 20, bold=True)
        self._font_hint   = pygame.font.SysFont('monospace', 13)
        self._font_alert  = pygame.font.SysFont('monospace', 28, bold=True)
        self._font_big    = pygame.font.SysFont('monospace', 46, bold=True)
        self._font_med    = pygame.font.SysFont('monospace', 22, bold=True)
        self._font_sub    = pygame.font.SysFont('monospace', 17)
        self._font_btn    = pygame.font.SysFont('monospace', 18, bold=True)
        self._font_sb_hdr = pygame.font.SysFont('segoeui',   14, bold=True)
        self._font_sb     = pygame.font.SysFont('segoeui',   13)
        self._font_sb_sm  = pygame.font.SysFont('segoeui',   11)

        self._bg_surface  = pygame.Surface((BOARD_W, BOARD_H))
        self._bg_dirty    = True

        self._overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 175))

        # tracking components
        self._turn_panel = TurnPanel()
        self._sidebar    = Sidebar(self._load_img)

    # ------------------------------------------------------------------ #
    #  IMAGE CACHE                                                         #
    # ------------------------------------------------------------------ #

    def _load_img(self, path):
        if path not in self._img_cache:
            self._img_cache[path] = pygame.image.load(path).convert_alpha()
        return self._img_cache[path]

    # ------------------------------------------------------------------ #
    #  DRAW — NỀN BÀN CỜ                                                  #
    # ------------------------------------------------------------------ #

    def _rebuild_bg(self):
        theme = self.config.theme
        surf  = self._bg_surface
        for row in range(ROWS):
            for col in range(COLS):
                color = theme.bg.light if (row + col) % 2 == 0 else theme.bg.dark
                pygame.draw.rect(surf, color, (col*SQSIZE, row*SQSIZE, SQSIZE, SQSIZE))
                if col == 0:
                    c   = theme.bg.dark if row % 2 == 0 else theme.bg.light
                    lbl = self._font_coord.render(str(ROWS-row), True, c)
                    surf.blit(lbl, (3, 3 + row*SQSIZE))
                if row == 7:
                    c   = theme.bg.dark if (row+col) % 2 == 0 else theme.bg.light
                    lbl = self._font_coord.render(Square.get_alphacol(col), True, c)
                    surf.blit(lbl, (col*SQSIZE + SQSIZE - 16, BOARD_H - 18))
        self._bg_dirty = False

    def show_bg(self, surface):
        if self._bg_dirty:
            self._rebuild_bg()
        surface.blit(self._bg_surface, (BOARD_OFFSET_X, BOARD_OFFSET_Y))

    # ------------------------------------------------------------------ #
    #  DRAW — QUÂN CỜ                                                      #
    # ------------------------------------------------------------------ #

    def show_pieces(self, surface):
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        for row in range(ROWS):
            for col in range(COLS):
                sq = self.board.squares[row][col]
                if sq.has_piece() and sq.piece is not self.dragger.piece:
                    piece = sq.piece
                    piece.set_texture(size=80)
                    img = self._load_img(piece.texture)
                    cx  = ox + col*SQSIZE + SQSIZE//2
                    cy  = oy + row*SQSIZE + SQSIZE//2
                    piece.texture_rect = img.get_rect(center=(cx, cy))
                    surface.blit(img, piece.texture_rect)

    def show_moves(self, surface):
        if not self.dragger.dragging:
            return
        if not self.config.show_hints:
            return
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        theme = self.config.theme
        for move in self.dragger.piece.moves:
            r, c  = move.final.row, move.final.col
            color = theme.moves.light if (r+c) % 2 == 0 else theme.moves.dark
            cx    = ox + c*SQSIZE + SQSIZE//2
            cy    = oy + r*SQSIZE + SQSIZE//2
            if self.board.squares[r][c].has_piece():
                pygame.draw.circle(surface, color, (cx, cy), SQSIZE//2 - 4, 7)
            else:
                pygame.draw.circle(surface, color, (cx, cy), SQSIZE//5)

    def show_last_move(self, surface):
        if not self.board.last_move:
            return
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        theme = self.config.theme
        for pos in [self.board.last_move.initial, self.board.last_move.final]:
            color = theme.trace.light if (pos.row+pos.col) % 2 == 0 else theme.trace.dark
            pygame.draw.rect(surface, color,
                             (ox + pos.col*SQSIZE, oy + pos.row*SQSIZE, SQSIZE, SQSIZE))

    def show_hover(self, surface):
        if self.hovered_sqr:
            ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
            pygame.draw.rect(surface, (180, 180, 180),
                             (ox + self.hovered_sqr.col*SQSIZE,
                              oy + self.hovered_sqr.row*SQSIZE,
                              SQSIZE, SQSIZE), width=3)

    def show_check(self, surface):
        if not self.in_check:
            return
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        for row in range(ROWS):
            for col in range(COLS):
                p = self.board.squares[row][col].piece
                if isinstance(p, King) and p.color == self.next_player:
                    t     = pygame.time.get_ticks() / 400.0
                    alpha = int(90 + 60 * math.sin(t))
                    s     = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    s.fill((220, 40, 40, alpha))
                    surface.blit(s, (ox + col*SQSIZE, oy + row*SQSIZE))
                    pygame.draw.rect(surface, COLOR_CHECK,
                                     (ox + col*SQSIZE, oy + row*SQSIZE, SQSIZE, SQSIZE), 3)

    # ------------------------------------------------------------------ #
    #  DRAW — ALERT                                                        #
    # ------------------------------------------------------------------ #

    def show_alert(self, surface):
        if self._alert_timer <= 0:
            return
        self._alert_timer -= 1
        progress = self._alert_timer / self._ALERT_DUR
        alpha    = min(255, int(255 * min(1.0, progress * 3)))
        ease     = 1 - (1 - min(1.0, (1.0 - progress) * 6)) ** 3
        y_off    = int(-60 * (1 - ease))
        pad_x, pad_y = 24, 12
        lbl = self._font_alert.render(self._alert_text, True, (255, 255, 255))
        w   = lbl.get_width()  + pad_x*2
        h   = lbl.get_height() + pad_y*2
        # căn giữa trên vùng bàn cờ
        x   = BOARD_OFFSET_X + BOARD_W//2 - w//2
        y   = BOARD_OFFSET_Y + BOARD_H//2 - h//2 + y_off
        popup = pygame.Surface((w, h), pygame.SRCALPHA)
        r, g, b = self._alert_color
        popup.fill((r, g, b, min(220, alpha)))
        pygame.draw.rect(popup, (255,255,255,min(180,alpha)),
                         popup.get_rect(), 2, border_radius=10)
        surface.blit(popup, (x, y))
        lbl_a = lbl.copy(); lbl_a.set_alpha(alpha)
        surface.blit(lbl_a, (x+pad_x, y+pad_y))

    # ------------------------------------------------------------------ #
    #  DRAW — TURN PANEL & SIDEBAR (delegated to tracking.py)             #
    # ------------------------------------------------------------------ #

    def show_turn_panel(self, surface):
        self._turn_panel.draw(surface, self.next_player, self.in_check,
                              len(self.board.move_log))

    def show_sidebar(self, surface):
        self._sidebar.draw(surface, self.next_player, self.in_check,
                           self.board.move_log, self.board.captured,
                           len(self.board.move_log))

    # ------------------------------------------------------------------ #
    #  DRAW — GAME OVER                                                    #
    # ------------------------------------------------------------------ #

    def show_gameover(self, surface):
        surface.blit(self._overlay, (0, 0))
        mid_x = WIDTH  // 2
        mid_y = HEIGHT // 2

        if self.game_result in (RESULT_CHECKMATE, RESULT_KING_DEAD):
            wn = 'Trang' if self.winner == 'white' else 'Den'
            ln = 'Den'   if self.winner == 'white' else 'Trang'
            crown = self._font_big.render(
                '[W]' if self.winner == 'white' else '[B]', True, (255,215,0))
            surface.blit(crown, crown.get_rect(center=(mid_x, mid_y-150)))
            title = self._font_big.render(f'{wn} THANG!', True, (255,215,0))
            surface.blit(title, title.get_rect(center=(mid_x, mid_y-90)))
            sub_txt = 'Chieu tuong!' if self.game_result == RESULT_CHECKMATE else 'Vua bi bat!'
            sub = self._font_med.render(sub_txt, True, COLOR_CHECK)
            surface.blit(sub, sub.get_rect(center=(mid_x, mid_y-45)))
            desc = self._font_sub.render(f'Vua {ln} da bi an', True, (200,200,200))
            surface.blit(desc, desc.get_rect(center=(mid_x, mid_y-10)))
        elif self.game_result == RESULT_STALEMATE:
            title = self._font_big.render('HOA CO!', True, (180,180,255))
            surface.blit(title, title.get_rect(center=(mid_x, mid_y-90)))
            sub = self._font_med.render('Stalemate', True, COLOR_STALEMATE)
            surface.blit(sub, sub.get_rect(center=(mid_x, mid_y-45)))
            pn = 'Trang' if self.next_player == 'white' else 'Den'
            desc = self._font_sub.render(f'{pn} khong con nuoc di', True, (200,200,200))
            surface.blit(desc, desc.get_rect(center=(mid_x, mid_y-10)))

        # thống kê nhanh
        wc = len(self.board.captured['white'])
        bc = len(self.board.captured['black'])
        stat = self._font_sub.render(
            f'Trang an: {wc} quan   Den an: {bc} quan', True, (180,180,200))
        surface.blit(stat, stat.get_rect(center=(mid_x, mid_y+18)))

        # 2 nút
        btn_w, btn_h = 210, 50
        gap   = 14
        bx    = mid_x - (btn_w*2+gap)//2
        by    = mid_y + 45
        mouse = pygame.mouse.get_pos()

        btn_reset = pygame.Rect(bx, by, btn_w, btn_h)
        cr = (70,190,70) if btn_reset.collidepoint(mouse) else (45,140,45)
        pygame.draw.rect(surface, cr, btn_reset, border_radius=12)
        pygame.draw.rect(surface, (255,255,255), btn_reset, 2, border_radius=12)
        lr = self._font_btn.render('Choi lai  (R)', True, (255,255,255))
        surface.blit(lr, lr.get_rect(center=btn_reset.center))

        btn_menu = pygame.Rect(bx+btn_w+gap, by, btn_w, btn_h)
        cm = (80,120,200) if btn_menu.collidepoint(mouse) else (50,90,170)
        pygame.draw.rect(surface, cm, btn_menu, border_radius=12)
        pygame.draw.rect(surface, (255,255,255), btn_menu, 2, border_radius=12)
        lm = self._font_btn.render('Ve Menu  (M)', True, (255,255,255))
        surface.blit(lm, lm.get_rect(center=btn_menu.center))

        return btn_reset, btn_menu

    # ------------------------------------------------------------------ #
    #  GAME LOGIC                                                          #
    # ------------------------------------------------------------------ #

    def check_king_captured(self):
        wa = ba = False
        for row in range(ROWS):
            for col in range(COLS):
                p = self.board.squares[row][col].piece
                if isinstance(p, King):
                    if p.color == 'white': wa = True
                    else:                  ba = True
        if not ba:
            self.winner = 'white'; self.game_result = RESULT_KING_DEAD
        elif not wa:
            self.winner = 'black'; self.game_result = RESULT_KING_DEAD

    def _trigger_alert(self, text, color):
        self._alert_text  = text
        self._alert_color = color
        self._alert_timer = self._ALERT_DUR

    def update_game_state(self):
        self.check_king_captured()
        if self.game_result != RESULT_NONE:
            return
        color     = self.next_player
        self.in_check = self.board.is_in_check(color)
        has_moves = self.board.has_any_valid_move(color)
        if not has_moves:
            if self.in_check:
                self.game_result = RESULT_CHECKMATE
                self.winner      = 'black' if color == 'white' else 'white'
            else:
                self.game_result = RESULT_STALEMATE
                self.winner      = None
        elif self.in_check:
            pn = 'Trang' if color == 'white' else 'Den'
            self._trigger_alert(f'! {pn} dang bi chieu !', COLOR_CHECK)

    def next_turn(self):
        self.next_player = 'white' if self.next_player == 'black' else 'black'
        self.update_game_state()

    def set_hover(self, row, col):
        self.hovered_sqr = self.board.squares[row][col]

    def change_theme(self):
        self.config.change_theme()
        self._bg_dirty = True

    def play_sound(self, captured=False):
        if captured:
            self.config.capture_sound.play()
        else:
            self.config.move_sound.play()

    def reset(self):
        self.__init__()

    @property
    def is_over(self):
        return self.game_result != RESULT_NONE
