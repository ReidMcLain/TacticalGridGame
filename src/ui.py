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
            f = self.font if i == 0 else self.small
            txt = f.render(line, True, WHITE if i == 0 else GRAY)
            surf.blit(txt, (12, y))
            y += 26