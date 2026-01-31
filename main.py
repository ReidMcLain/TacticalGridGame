import pygame
from src.constants import FPS, TILE_SIZE, UI_H
from src.ui import UI
from src.game import Game
from src.units import init_assets

def main():
    pygame.init()
    pygame.display.set_caption("GRIDS v0.1")
    clock = pygame.time.Clock()

    ui = UI()
    game = Game(ui)

    screen = pygame.display.set_mode(
        (game.grid.w * TILE_SIZE, game.grid.h * TILE_SIZE + UI_H)
    )

    init_assets()

    running = True
    while running:
        dt_ms = clock.tick(FPS)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(e)

        game.update(dt_ms)
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()