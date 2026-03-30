import pygame
import sys

from const import *
from game import Game
from square import Square
from move import Move

FPS = 60


class Main:

    def __init__(self, screen: pygame.Surface = None):
        pygame.init()
        if screen is not None:
            # dùng lại surface từ menu — không tạo lại display
            self.screen = screen
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
        pygame.display.set_caption('Chess')
        self.clock       = pygame.time.Clock()
        self.game        = Game()
        self.exit_signal = None   # 'menu' | None

    def _new_game(self):
        self.game = Game()

    def _draw_frame(self):
        game   = self.game
        screen = self.screen

        # fill vùng ngoài bàn cờ (sidebar + panel dưới sidebar)
        screen.fill((18, 18, 30))

        game.show_bg(screen)
        game.show_last_move(screen)
        game.show_moves(screen)
        game.show_pieces(screen)
        game.show_hover(screen)
        game.show_check(screen)

        if game.dragger.dragging:
            game.dragger.update_blit(screen, game._img_cache)

        game.show_turn_panel(screen)
        game.show_sidebar(screen)
        game.show_alert(screen)

        if game.is_over:
            self._btn_reset, self._btn_menu = game.show_gameover(screen)

    def mainloop(self):
        self._btn_reset = None
        self._btn_menu  = None

        while True:
            game    = self.game
            board   = game.board
            dragger = game.dragger

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.exit_signal = 'menu'
                        return
                    if event.key == pygame.K_r:
                        self._new_game()
                        continue
                    if event.key == pygame.K_m:
                        self.exit_signal = 'menu'
                        return
                    if event.key == pygame.K_t and not game.is_over:
                        game.change_theme()

                if game.is_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self._btn_reset and self._btn_reset.collidepoint(event.pos):
                            self._new_game()
                        elif self._btn_menu and self._btn_menu.collidepoint(event.pos):
                            self.exit_signal = 'menu'
                            return
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    dragger.update_mouse(event.pos)
                    # trừ offset để ra tọa độ trong bàn cờ
                    r = (dragger.mouseY - BOARD_OFFSET_Y) // SQSIZE
                    c = (dragger.mouseX - BOARD_OFFSET_X) // SQSIZE
                    if not Square.in_range(r, c):
                        continue
                    sq = board.squares[r][c]
                    if sq.has_piece() and sq.piece.color == game.next_player:
                        board.calc_moves(sq.piece, r, c, bool=True)
                        dragger.save_initial(event.pos)
                        dragger.drag_piece(sq.piece)

                elif event.type == pygame.MOUSEMOTION:
                    r = (event.pos[1] - BOARD_OFFSET_Y) // SQSIZE
                    c = (event.pos[0] - BOARD_OFFSET_X) // SQSIZE
                    if Square.in_range(r, c):
                        game.set_hover(r, c)
                    else:
                        game.hovered_sqr = None
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        r = (dragger.mouseY - BOARD_OFFSET_Y) // SQSIZE
                        c = (dragger.mouseX - BOARD_OFFSET_X) // SQSIZE
                        if Square.in_range(r, c):
                            initial = Square(dragger.initial_row, dragger.initial_col)
                            final   = Square(r, c)
                            move    = Move(initial, final)
                            if board.valid_move(dragger.piece, move):
                                captured = board.squares[r][c].has_piece()
                                board.move(dragger.piece, move)
                                board.set_true_en_passant(dragger.piece)
                                game.play_sound(captured)
                                game.next_turn()
                    dragger.undrag_piece()

            self._draw_frame()
            pygame.display.flip()
            self.clock.tick(FPS)


def launch(on_menu=None, screen=None, apply_settings=None):
    """Khởi động game. Truyền screen để tái sử dụng surface từ menu."""
    m = Main(screen=screen)
    if apply_settings:
        apply_settings(m.game)
    m.mainloop()
    if m.exit_signal == 'menu':
        if on_menu:
            on_menu()
        else:
            pygame.quit()
            sys.exit()


if __name__ == '__main__':
    launch()
