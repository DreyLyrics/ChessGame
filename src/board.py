from const import *
from square import Square
from piece import *
from move import Move
import copy


class Board:

    def __init__(self):
        self.squares   = [[0]*COLS for _ in range(ROWS)]
        self.last_move = None
        self.move_log  = []
        self.captured  = {'white': [], 'black': []}

        self._create()
        self._add_pieces('white')
        self._add_pieces('black')

    # ------------------------------------------------------------------ #
    #  MOVE EXECUTION                                                      #
    # ------------------------------------------------------------------ #

    def move(self, piece, move, testing=False):
        initial = move.initial
        final   = move.final

        en_passant_empty = self.squares[final.row][final.col].isempty()
        captured_piece   = self.squares[final.row][final.col].piece

        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        if isinstance(piece, Pawn):
            diff = final.col - initial.col
            if diff != 0 and en_passant_empty:
                ep_piece = self.squares[initial.row][initial.col + diff].piece
                if ep_piece and not testing:
                    self.captured[piece.color].append(ep_piece.name)
                self.squares[initial.row][initial.col + diff].piece = None
                captured_piece = ep_piece
            else:
                self.check_promotion(piece, final)

        if isinstance(piece, King):
            if self.castling(initial, final) and not testing:
                diff = final.col - initial.col
                rook = piece.left_rook if diff < 0 else piece.right_rook
                if rook:
                    self.move(rook, rook.moves[-1])

        if not testing:
            cap_name = captured_piece.name if captured_piece else None
            if cap_name:
                self.captured[piece.color].append(cap_name)
            from_sq = Square.get_alphacol(initial.col) + str(ROWS - initial.row)
            to_sq   = Square.get_alphacol(final.col)   + str(ROWS - final.row)
            self.move_log.append((piece.name, piece.color, from_sq, to_sq, cap_name))

        piece.moved = True
        piece.clear_moves()
        self.last_move = move

    def valid_move(self, piece, move):
        return move in piece.moves

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2

    def set_true_en_passant(self, piece):
        if not isinstance(piece, Pawn):
            return
        for row in range(ROWS):
            for col in range(COLS):
                p = self.squares[row][col].piece
                if isinstance(p, Pawn) and p.color == piece.color:
                    p.en_passant = False
        if self.last_move:
            if abs(self.last_move.final.row - self.last_move.initial.row) == 2:
                piece.en_passant = True

    # ------------------------------------------------------------------ #
    #  CHECK DETECTION (dùng cho hiển thị cảnh báo, không chặn nước đi)  #
    # ------------------------------------------------------------------ #

    def in_check(self, piece, move):
        """Kiểm tra nước đi có để vua bị chiếu không (chỉ dùng nội bộ)."""
        temp_piece = copy.deepcopy(piece)
        temp_board = copy.deepcopy(self)
        temp_board.move(temp_piece, move, testing=True)
        for row in range(ROWS):
            for col in range(COLS):
                if temp_board.squares[row][col].has_enemy_piece(piece.color):
                    p = temp_board.squares[row][col].piece
                    temp_board.calc_moves(p, row, col)
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
                            return True
        return False

    def is_in_check(self, color):
        """Kiểm tra vua màu color có đang bị chiếu không."""
        for row in range(ROWS):
            for col in range(COLS):
                if self.squares[row][col].has_enemy_piece(color):
                    p = self.squares[row][col].piece
                    p.clear_moves()
                    self.calc_moves(p, row, col)
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
                            p.clear_moves()
                            return True
                    p.clear_moves()
        return False

    def has_any_valid_move(self, color):
        for row in range(ROWS):
            for col in range(COLS):
                if self.squares[row][col].has_team_piece(color):
                    p = self.squares[row][col].piece
                    p.clear_moves()
                    self.calc_moves(p, row, col)
                    has = len(p.moves) > 0
                    p.clear_moves()
                    if has:
                        return True
        return False

    # ------------------------------------------------------------------ #
    #  MOVE CALCULATION — không lọc chiếu, di chuyển tự do               #
    # ------------------------------------------------------------------ #

    def calc_moves(self, piece, row, col, bool=True):
        """Tính tất cả nước đi hợp lệ. bool không còn dùng để lọc chiếu."""

        def pawn_moves():
            steps = 1 if piece.moved else 2
            start = row + piece.dir
            end   = row + piece.dir * (1 + steps)
            for r in range(start, end, piece.dir):
                if not Square.in_range(r):
                    break
                if self.squares[r][col].isempty():
                    piece.add_move(Move(Square(row, col), Square(r, col)))
                else:
                    break
            for dc in [-1, 1]:
                r, c = row + piece.dir, col + dc
                if Square.in_range(r, c) and self.squares[r][c].has_enemy_piece(piece.color):
                    fp = self.squares[r][c].piece
                    piece.add_move(Move(Square(row, col), Square(r, c, fp)))
            ep_row       = 3 if piece.color == 'white' else 4
            ep_final_row = 2 if piece.color == 'white' else 5
            if row == ep_row:
                for dc in [-1, 1]:
                    c = col + dc
                    if Square.in_range(c):
                        adj = self.squares[row][c].piece
                        if isinstance(adj, Pawn) and adj.color != piece.color and adj.en_passant:
                            piece.add_move(Move(Square(row, col), Square(ep_final_row, c, adj)))

        def knight_moves():
            for dr, dc in [(-2,1),(-1,2),(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1)]:
                r, c = row+dr, col+dc
                if Square.in_range(r, c) and self.squares[r][c].isempty_or_enemy(piece.color):
                    fp = self.squares[r][c].piece
                    piece.add_move(Move(Square(row, col), Square(r, c, fp)))

        def straightline_moves(incrs):
            for ri, ci in incrs:
                r, c = row+ri, col+ci
                while True:
                    if not Square.in_range(r, c):
                        break
                    fp = self.squares[r][c].piece
                    if self.squares[r][c].isempty():
                        piece.add_move(Move(Square(row, col), Square(r, c, fp)))
                    elif self.squares[r][c].has_enemy_piece(piece.color):
                        piece.add_move(Move(Square(row, col), Square(r, c, fp)))
                        break
                    else:
                        break
                    r += ri; c += ci

        def king_moves():
            for r, c in [(row-1,col),(row-1,col+1),(row,col+1),(row+1,col+1),
                         (row+1,col),(row+1,col-1),(row,col-1),(row-1,col-1)]:
                if Square.in_range(r, c) and self.squares[r][c].isempty_or_enemy(piece.color):
                    piece.add_move(Move(Square(row, col), Square(r, c)))
            # nhập thành — chỉ khi vua chưa di chuyển
            if not piece.moved:
                # nhập thành trái (queen-side)
                lr = self.squares[row][0].piece
                if isinstance(lr, Rook) and not lr.moved:
                    if all(self.squares[row][c].isempty() for c in range(1, 4)):
                        piece.left_rook = lr
                        lr.add_move(Move(Square(row, 0), Square(row, 3)))
                        piece.add_move(Move(Square(row, col), Square(row, 2)))
                # nhập thành phải (king-side)
                rr = self.squares[row][7].piece
                if isinstance(rr, Rook) and not rr.moved:
                    if all(self.squares[row][c].isempty() for c in range(5, 7)):
                        piece.right_rook = rr
                        rr.add_move(Move(Square(row, 7), Square(row, 5)))
                        piece.add_move(Move(Square(row, col), Square(row, 6)))

        if isinstance(piece, Pawn):     pawn_moves()
        elif isinstance(piece, Knight): knight_moves()
        elif isinstance(piece, Bishop): straightline_moves([(-1,1),(-1,-1),(1,1),(1,-1)])
        elif isinstance(piece, Rook):   straightline_moves([(-1,0),(0,1),(1,0),(0,-1)])
        elif isinstance(piece, Queen):  straightline_moves([(-1,1),(-1,-1),(1,1),(1,-1),(-1,0),(0,1),(1,0),(0,-1)])
        elif isinstance(piece, King):   king_moves()

    # ------------------------------------------------------------------ #
    #  BOARD SETUP                                                         #
    # ------------------------------------------------------------------ #

    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        rp, ro = (6, 7) if color == 'white' else (1, 0)
        for col in range(COLS):
            self.squares[rp][col] = Square(rp, col, Pawn(color))
        self.squares[ro][1] = Square(ro, 1, Knight(color))
        self.squares[ro][6] = Square(ro, 6, Knight(color))
        self.squares[ro][2] = Square(ro, 2, Bishop(color))
        self.squares[ro][5] = Square(ro, 5, Bishop(color))
        self.squares[ro][0] = Square(ro, 0, Rook(color))
        self.squares[ro][7] = Square(ro, 7, Rook(color))
        self.squares[ro][3] = Square(ro, 3, Queen(color))
        self.squares[ro][4] = Square(ro, 4, King(color))
