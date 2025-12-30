import pygame
from .constants import SCREEN_W, SCREEN_H, UI_H, DARK, WHITE, GRAY

class UI:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small = pygame.font.SysFont("consolas", 18)

    def draw_panel(self, surf, lines):
        panel = pygame.Rect(0, SCREEN_H - UI_H, SCREEN_W, UI_H)
        pygame.draw.rect(surf, DARK, panel)

        y = panel.y + 10
        for i, line in enumerate(lines):
            font = self.font if i == 0 else self.small
            color = WHITE if i == 0 else GRAY
            txt = font.render(line, True, color)
            surf.blit(txt, (12, y))
            y += 24