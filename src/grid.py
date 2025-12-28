import pygame
from collections import deque
from .constants import GRID_W, GRID_H, TILE_SIZE, TILE_COLORS, TILES, BLACK

class Grid:
    def __init__(self):
        self.w = GRID_W
        self.h = GRID_H
        self.tiles = [["PLAIN" for _ in range(self.w)] for _ in range(self.h)]
        self._seed_map()

    def _seed_map(self):
        preset = [
            ["PLAIN","PLAIN","FOREST","PLAIN","HILL","PLAIN"],
            ["PLAIN","WATER","WATER","PLAIN","HILL","PLAIN"],
            ["PLAIN","PLAIN","FOREST","PLAIN","PLAIN","PLAIN"],
            ["HILL","PLAIN","PLAIN","PLAIN","FOREST","PLAIN"],
            ["PLAIN","PLAIN","PLAIN","WATER","WATER","PLAIN"],
            ["PLAIN","HILL","PLAIN","PLAIN","PLAIN","PLAIN"],
        ]
        for y in range(self.h):
            for x in range(self.w):
                self.tiles[y][x] = preset[y][x]

    def in_bounds(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def tile_type(self, x, y):
        return self.tiles[y][x]

    def move_cost(self, x, y):
        t = self.tile_type(x, y)
        return TILES[t]["move_cost"]

    def def_bonus(self, x, y):
        t = self.tile_type(x, y)
        return TILES[t]["def_bonus"]

    def cell_from_pixel(self, px, py):
        if py >= self.h * TILE_SIZE:
            return None
        x = px // TILE_SIZE
        y = py // TILE_SIZE
        if not self.in_bounds(x, y):
            return None
        return (x, y)

    def cell_rect(self, x, y):
        return pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def neighbors4(self, x, y):
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                yield (nx, ny)

    def draw(self, surf):
        for y in range(self.h):
            for x in range(self.w):
                t = self.tile_type(x, y)
                r = self.cell_rect(x, y)
                pygame.draw.rect(surf, TILE_COLORS[t], r)
                pygame.draw.rect(surf, BLACK, r, 1)

    def reachable_cells(self, start, move_points, blocked_cells):
        sx, sy = start
        dist = { (sx, sy): 0 }
        q = deque([(sx, sy)])

        while q:
            x, y = q.popleft()
            for nx, ny in self.neighbors4(x, y):
                cost = self.move_cost(nx, ny)
                if cost >= 999:
                    continue
                nd = dist[(x, y)] + cost
                if nd > move_points:
                    continue
                if (nx, ny) in blocked_cells and (nx, ny) != (sx, sy):
                    continue
                if (nx, ny) not in dist or nd < dist[(nx, ny)]:
                    dist[(nx, ny)] = nd
                    q.append((nx, ny))

        return set(dist.keys())