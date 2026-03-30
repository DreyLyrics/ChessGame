"""
LocalBattle/LocalBattle.py
Chế độ Local — 2 người chơi trên cùng 1 máy.
Chạy src/main.py trực tiếp, không thay đổi gì thêm.
"""

import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC  = os.path.join(os.path.dirname(_HERE), 'src')
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from main import launch


def launch_local(on_menu=None, screen=None, apply_settings=None):
    """Khởi động chế độ Local (PVP cùng máy)."""
    launch(on_menu=on_menu, screen=screen, apply_settings=apply_settings)


if __name__ == '__main__':
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
    pygame.display.set_caption('Chess  |  Local')
    launch_local(screen=screen)
