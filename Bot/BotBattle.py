"""
Bot/BotBattle.py
Chế độ Người (Trắng) vs Bot Stockfish (Đen).
Chạy trên engine đồ họa của src/main.py.

Chạy trực tiếp : python Bot/BotBattle.py
Gọi từ menu   : from Bot.BotBattle import launch_bot
"""

import sys
import os
import threading
import pygame

# ── path setup ───────────────────────────────────────────────────────────────
_BOT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(os.path.dirname(_BOT_DIR), 'src')
for _p in (_SRC_DIR, _BOT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── import src (chỉ import, không sửa) ───────────────────────────────────────
from const  import *
from game   import Game
from square import Square
from move   import Move
from piece  import Pawn, King, Rook

# ── import BotChess ───────────────────────────────────────────────────────────
from BotChess import get_bot_move, quit_engine

FPS = 60


# ── Board → FEN ──────────────────────────────────────────────────────────────

_PIECE_FEN = {
    ('pawn',   'white'): 'P', ('pawn',   'black'): 'p',
    ('knight', 'white'): 'N', ('knight', 'black'): 'n',
    ('bishop', 'white'): 'B', ('bishop', 'black'): 'b',
    ('rook',   'white'): 'R', ('rook',   'black'): 'r',
    ('queen',  'white'): 'Q', ('queen',  'black'): 'q',
    ('king',   'white'): 'K', ('king',   'black'): 'k',
}


def board_to_fen(board, next_player: str) -> str:
    """Tạo FEN string từ Board của game."""
    rows = []
    for row in range(ROWS):
        empty, s = 0, ''
        for col in range(COLS):
            p = board.squares[row][col].piece
            if p is None:
                empty += 1
            else:
                if empty:
                    s += str(empty)
                    empty = 0
                s += _PIECE_FEN[(p.name, p.color)]
        if empty:
            s += str(empty)
        rows.append(s)

    turn = 'w' if next_player == 'white' else 'b'

    # castling rights
    castling = ''
    for color, row in [('white', 7), ('black', 0)]:
        king = board.squares[row][4].piece
        if isinstance(king, King) and not king.moved:
            rr = board.squares[row][7].piece
            if isinstance(rr, Rook) and not rr.moved:
                castling += 'K' if color == 'white' else 'k'
            lr = board.squares[row][0].piece
            if isinstance(lr, Rook) and not lr.moved:
                castling += 'Q' if color == 'white' else 'q'
    if not castling:
        castling = '-'

    # en passant
    ep = '-'
    if board.last_move:
        lm = board.last_move
        p  = board.squares[lm.final.row][lm.final.col].piece
        if isinstance(p, Pawn) and abs(lm.final.row - lm.initial.row) == 2:
            ep_row = (lm.final.row + lm.initial.row) // 2
            ep = Square.get_alphacol(lm.final.col) + str(ROWS - ep_row)

    fullmove = len(board.move_log) // 2 + 1
    return f'{"/".join(rows)} {turn} {castling} {ep} 0 {fullmove}'


# ── UCI string → game Move ────────────────────────────────────────────────────

_COL_MAP = {'a':0,'b':1,'c':2,'d':3,'e':4,'f':5,'g':6,'h':7}


def uci_to_game_move(uci):
    """Chuyển UCI string (vd 'e2e4') → Move của game."""
    if not uci or len(uci) < 4:
        return None
    try:
        fc = _COL_MAP[uci[0]]; fr = ROWS - int(uci[1])
        tc = _COL_MAP[uci[2]]; tr = ROWS - int(uci[3])
    except (KeyError, ValueError):
        return None
    if not (Square.in_range(fr, fc) and Square.in_range(tr, tc)):
        return None
    return Move(Square(fr, fc), Square(tr, tc))


# ── BotMain ───────────────────────────────────────────────────────────────────

class BotMain:
    """
    Vòng lặp game giống src/main.py nhưng thêm bot Stockfish.
    human_color: 'white' | 'black' — màu người chơi chọn
    """

    BOT_DELAY = 350

    def __init__(self, screen=None, human_color='white'):
        pygame.init()
        self.screen     = screen or pygame.display.set_mode((0, 0), pygame.NOFRAME)
        self.HUMAN_COLOR = human_color
        self.BOT_COLOR   = 'black' if human_color == 'white' else 'white'
        pygame.display.set_caption(
            f'Chess vs Bot  |  Ban = {"Trang" if human_color == "white" else "Den"}'
        )
        self.clock        = pygame.time.Clock()
        self.game         = Game()
        self.exit_signal  = None
        self._btn_reset   = None
        self._btn_menu    = None
        self._bot_timer   = 0
        self._pending_uci = None   # nước đi bot tính xong, chờ thực thi
        self._thinking    = False

    # ── helpers ───────────────────────────────────────────────────────────────

    def _new_game(self):
        self.game         = Game()
        self._bot_timer   = 0
        self._pending_uci = None
        self._thinking    = False

    def _map_pos(self, pos):
        """Khi chơi Đen: đảo tọa độ chuột để khớp với bàn cờ flip."""
        x, y = pos
        if self.HUMAN_COLOR == 'black':
            bx, by = BOARD_OFFSET_X, BOARD_OFFSET_Y
            if bx <= x <= bx + BOARD_W and by <= y <= by + BOARD_H:
                x = bx + BOARD_W - (x - bx)
                y = by + BOARD_H - (y - by)
        return (x, y)

    def _draw_frame(self):
        g = self.game
        s = self.screen
        s.fill((18, 18, 30))
        flip = (self.HUMAN_COLOR == 'black')

        g.show_bg(s)
        self._show_last_move_flip(s, flip)
        self._show_moves_flip(s, flip)
        self._show_pieces_flip(s, flip)
        self._show_hover_flip(s, flip)
        self._show_check_flip(s, flip)
        if g.dragger.dragging:
            g.dragger.update_blit(s, g._img_cache)

        g.show_turn_panel(s)
        g.show_sidebar(s)
        g.show_alert(s)
        if g.is_over:
            self._btn_reset, self._btn_menu = g.show_gameover(s)

    # ── flip helpers ──────────────────────────────────────────────────────────

    def _fr(self, row, flip):
        """Chuyển row thật → row hiển thị."""
        return (ROWS - 1 - row) if flip else row

    def _fc(self, col, flip):
        return (COLS - 1 - col) if flip else col

    def _show_pieces_flip(self, surface, flip):
        g = self.game
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        for row in range(ROWS):
            for col in range(COLS):
                sq = g.board.squares[row][col]
                if sq.has_piece() and sq.piece is not g.dragger.piece:
                    piece = sq.piece
                    piece.set_texture(size=80)
                    img = g._load_img(piece.texture)
                    dr, dc = self._fr(row, flip), self._fc(col, flip)
                    cx = ox + dc * SQSIZE + SQSIZE // 2
                    cy = oy + dr * SQSIZE + SQSIZE // 2
                    piece.texture_rect = img.get_rect(center=(cx, cy))
                    surface.blit(img, piece.texture_rect)

    def _show_moves_flip(self, surface, flip):
        g = self.game
        if not g.dragger.dragging or not g.config.show_hints:
            return
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        theme = g.config.theme
        for move in g.dragger.piece.moves:
            r, c = move.final.row, move.final.col
            dr, dc = self._fr(r, flip), self._fc(c, flip)
            color = theme.moves.light if (r + c) % 2 == 0 else theme.moves.dark
            cx = ox + dc * SQSIZE + SQSIZE // 2
            cy = oy + dr * SQSIZE + SQSIZE // 2
            if g.board.squares[r][c].has_piece():
                pygame.draw.circle(surface, color, (cx, cy), SQSIZE // 2 - 4, 7)
            else:
                pygame.draw.circle(surface, color, (cx, cy), SQSIZE // 5)

    def _show_last_move_flip(self, surface, flip):
        g = self.game
        if not g.board.last_move:
            return
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        theme = g.config.theme
        for pos in [g.board.last_move.initial, g.board.last_move.final]:
            dr = self._fr(pos.row, flip)
            dc = self._fc(pos.col, flip)
            color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
            pygame.draw.rect(surface, color,
                             (ox + dc * SQSIZE, oy + dr * SQSIZE, SQSIZE, SQSIZE))

    def _show_hover_flip(self, surface, flip):
        g = self.game
        if not g.hovered_sqr:
            return
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        dr = self._fr(g.hovered_sqr.row, flip)
        dc = self._fc(g.hovered_sqr.col, flip)
        pygame.draw.rect(surface, (180, 180, 180),
                         (ox + dc * SQSIZE, oy + dr * SQSIZE, SQSIZE, SQSIZE), width=3)

    def _show_check_flip(self, surface, flip):
        import math as _math
        g = self.game
        if not g.in_check:
            return
        ox, oy = BOARD_OFFSET_X, BOARD_OFFSET_Y
        from piece import King
        for row in range(ROWS):
            for col in range(COLS):
                p = g.board.squares[row][col].piece
                if isinstance(p, King) and p.color == g.next_player:
                    dr = self._fr(row, flip)
                    dc = self._fc(col, flip)
                    t     = pygame.time.get_ticks() / 400.0
                    alpha = int(90 + 60 * _math.sin(t))
                    s     = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    s.fill((220, 40, 40, alpha))
                    surface.blit(s, (ox + dc * SQSIZE, oy + dr * SQSIZE))
                    pygame.draw.rect(surface, (220, 50, 50),
                                     (ox + dc * SQSIZE, oy + dr * SQSIZE, SQSIZE, SQSIZE), 3)

    # ── bot ───────────────────────────────────────────────────────────────────

    def _request_bot_move(self):
        """Tính nước đi Stockfish trong thread riêng — không block UI."""
        fen = board_to_fen(self.game.board, self.BOT_COLOR)
        self._thinking = True

        def _think():
            uci = get_bot_move(fen)
            self._pending_uci = uci
            self._thinking    = False

        threading.Thread(target=_think, daemon=True).start()

    def _apply_bot_move(self, uci: str):
        gm = uci_to_game_move(uci)
        if gm is None:
            return
        board = self.game.board
        sq    = board.squares[gm.initial.row][gm.initial.col]
        if not sq.has_piece() or sq.piece.color != self.BOT_COLOR:
            return
        board.calc_moves(sq.piece, gm.initial.row, gm.initial.col, bool=True)
        if board.valid_move(sq.piece, gm):
            captured = board.squares[gm.final.row][gm.final.col].has_piece()
            board.move(sq.piece, gm)
            board.set_true_en_passant(sq.piece)
            self.game.play_sound(captured)
            self.game.next_turn()

    # ── main loop ─────────────────────────────────────────────────────────────

    def mainloop(self):
        while True:
            game    = self.game
            board   = game.board
            dragger = game.dragger
            now     = pygame.time.get_ticks()

            # lượt bot
            if not game.is_over and game.next_player == self.BOT_COLOR and not dragger.dragging:
                if self._pending_uci is not None:
                    self._apply_bot_move(self._pending_uci)
                    self._pending_uci = None
                    self._bot_timer   = 0
                elif not self._thinking:
                    if self._bot_timer == 0:
                        self._bot_timer = now + self.BOT_DELAY
                    elif now >= self._bot_timer:
                        self._request_bot_move()

            # sự kiện
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    quit_engine()
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_m):
                        self.exit_signal = 'menu'
                        quit_engine()
                        return
                    if event.key == pygame.K_r:
                        self._new_game(); continue
                    if event.key == pygame.K_t and not game.is_over:
                        game.change_theme()

                if game.is_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self._btn_reset and self._btn_reset.collidepoint(event.pos):
                            self._new_game()
                        elif self._btn_menu and self._btn_menu.collidepoint(event.pos):
                            self.exit_signal = 'menu'
                            quit_engine()
                            return
                    continue

                # chỉ nhận input khi đến lượt người
                if game.next_player != self.HUMAN_COLOR:
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mapped = self._map_pos(event.pos)
                    dragger.update_mouse(mapped)
                    r = (dragger.mouseY - BOARD_OFFSET_Y) // SQSIZE
                    c = (dragger.mouseX - BOARD_OFFSET_X) // SQSIZE
                    if not Square.in_range(r, c):
                        continue
                    sq = board.squares[r][c]
                    if sq.has_piece() and sq.piece.color == self.HUMAN_COLOR:
                        board.calc_moves(sq.piece, r, c, bool=True)
                        dragger.save_initial(mapped)
                        dragger.drag_piece(sq.piece)

                elif event.type == pygame.MOUSEMOTION:
                    mapped = self._map_pos(event.pos)
                    r = (mapped[1] - BOARD_OFFSET_Y) // SQSIZE
                    c = (mapped[0] - BOARD_OFFSET_X) // SQSIZE
                    game.set_hover(r, c) if Square.in_range(r, c) else setattr(game, 'hovered_sqr', None)
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)   # vị trí thật để vẽ quân kéo

                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging:
                        mapped = self._map_pos(event.pos)
                        dragger.update_mouse(mapped)
                        r = (dragger.mouseY - BOARD_OFFSET_Y) // SQSIZE
                        c = (dragger.mouseX - BOARD_OFFSET_X) // SQSIZE
                        if Square.in_range(r, c):
                            mv = Move(Square(dragger.initial_row, dragger.initial_col),
                                      Square(r, c))
                            if board.valid_move(dragger.piece, mv):
                                captured = board.squares[r][c].has_piece()
                                board.move(dragger.piece, mv)
                                board.set_true_en_passant(dragger.piece)
                                game.play_sound(captured)
                                game.next_turn()
                                self._bot_timer = 0
                                self._pending_uci = None
                    dragger.undrag_piece()

            self._draw_frame()
            pygame.display.flip()
            self.clock.tick(FPS)


# ── entry point ───────────────────────────────────────────────────────────────

def launch_bot(on_menu=None, screen=None, human_color='white', apply_settings=None):
    """Khởi động chế độ vs Bot. human_color: 'white' | 'black'."""
    m = BotMain(screen=screen, human_color=human_color)
    if apply_settings:
        apply_settings(m.game)
    m.mainloop()
    if m.exit_signal == 'menu' and on_menu:
        on_menu()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
    launch_bot(screen=screen)
