import pygame

pygame.init()
_info = pygame.display.Info()

SCREEN_W = _info.current_w
SCREEN_H = _info.current_h

ROWS = 8
COLS = 8

PANEL_HEIGHT = 56
SIDEBAR_W    = 300

# SQSIZE: bàn cờ vừa chiều cao (trừ panel)
SQSIZE  = (SCREEN_H - PANEL_HEIGHT) // ROWS
BOARD_W = SQSIZE * COLS
BOARD_H = SQSIZE * ROWS

# Nếu bàn cờ + sidebar vượt chiều rộng → thu nhỏ
if BOARD_W + SIDEBAR_W > SCREEN_W:
    SQSIZE  = (SCREEN_W - SIDEBAR_W) // COLS
    BOARD_W = SQSIZE * COLS
    BOARD_H = SQSIZE * ROWS

# Căn toàn bộ (bàn cờ + sidebar) vào giữa màn hình theo chiều ngang
TOTAL_W      = BOARD_W + SIDEBAR_W
BOARD_OFFSET_X = (SCREEN_W - TOTAL_W) // 2   # lề trái để căn giữa
SIDEBAR_X    = BOARD_OFFSET_X + BOARD_W       # x bắt đầu sidebar

# Căn giữa theo chiều dọc (bàn cờ + panel)
BOARD_OFFSET_Y = (SCREEN_H - BOARD_H - PANEL_HEIGHT) // 2
PANEL_Y        = BOARD_OFFSET_Y + BOARD_H     # y bắt đầu panel lượt

WIDTH  = SCREEN_W
HEIGHT = SCREEN_H
