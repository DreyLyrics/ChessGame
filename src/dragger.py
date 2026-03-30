import pygame
from const import *

class Dragger:

    def __init__(self):
        self.piece = None
        self.dragging = False
        self.mouseX = 0
        self.mouseY = 0
        self.initial_row = 0
        self.initial_col = 0

    def update_blit(self, surface, img_cache):
        self.piece.set_texture(size=128)
        img = img_cache.get(self.piece.texture)
        if img is None:
            img = pygame.image.load(self.piece.texture).convert_alpha()
            img_cache[self.piece.texture] = img
        img_center = (self.mouseX, self.mouseY)
        self.piece.texture_rect = img.get_rect(center=img_center)
        surface.blit(img, self.piece.texture_rect)

    def update_mouse(self, pos):
        self.mouseX, self.mouseY = pos

    def save_initial(self, pos):
        self.initial_row = (pos[1] - BOARD_OFFSET_Y) // SQSIZE
        self.initial_col = (pos[0] - BOARD_OFFSET_X) // SQSIZE

    def drag_piece(self, piece):
        self.piece = piece
        self.dragging = True

    def undrag_piece(self):
        self.piece = None
        self.dragging = False
