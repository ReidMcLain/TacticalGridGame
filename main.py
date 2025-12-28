import pygame
from src.constants import SCREEN_W, SCREEN_H, FPS
from src.ui import UI
from src.game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("GRIDS v0.01")
    clock = pygame.time.Clock()

    ui = UI()
    game = Game(ui)

    running = True
    while running:
        dt = clock.tick(FPS)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(e)

        game.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()