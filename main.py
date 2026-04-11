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

    base_width = game.grid.w * TILE_SIZE
    base_height = game.grid.h * TILE_SIZE + UI_H
    base_size = (base_width, base_height)

    window = pygame.display.set_mode(base_size, pygame.RESIZABLE)
    game_surface = pygame.Surface(base_size)

    init_assets()

    running = True
    while running:
        dt_ms = clock.tick(FPS)

        window_w, window_h = window.get_size()
        scale = min(window_w / base_width, window_h / base_height)
        scaled_w = int(base_width * scale)
        scaled_h = int(base_height * scale)
        x_offset = (window_w - scaled_w) // 2
        y_offset = (window_h - scaled_h) // 2

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                mx, my = e.pos

                if x_offset <= mx < x_offset + scaled_w and y_offset <= my < y_offset + scaled_h:
                    game_x = int((mx - x_offset) / scale)
                    game_y = int((my - y_offset) / scale)

                    if e.type == pygame.MOUSEMOTION:
                        remapped_event = pygame.event.Event(
                            e.type,
                            {
                                "pos": (game_x, game_y),
                                "rel": e.rel,
                                "buttons": e.buttons
                            }
                        )
                    else:
                        remapped_event = pygame.event.Event(
                            e.type,
                            {
                                "pos": (game_x, game_y),
                                "button": e.button
                            }
                        )

                    game.handle_event(remapped_event)

            else:
                game.handle_event(e)

        game.update(dt_ms)
        game.draw(game_surface)

        scaled_surface = pygame.transform.scale(game_surface, (scaled_w, scaled_h))

        window.fill((0, 0, 0))
        window.blit(scaled_surface, (x_offset, y_offset))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()