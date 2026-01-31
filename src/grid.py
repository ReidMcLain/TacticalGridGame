import pygame
import os
from collections import deque
from .constants import GRID_W, GRID_H, TILE_SIZE, SUBTILE_SIZE, TILES, ASSETS_DIR

class Grid:
    def __init__(self):
        self.w = GRID_W
        self.h = GRID_H
        self.tiles = [["PLAIN" for _ in range(self.w)] for _ in range(self.h)]
        self.paint_w = self.w * 2
        self.paint_h = self.h * 2
        self.paint = [["P" for _ in range(self.paint_w)] for _ in range(self.paint_h)]
        self._seed_map()
        self._load_tiles()

    def _load_tiles(self):
        def load(name):
            img = pygame.image.load(os.path.join(ASSETS_DIR, name))
            if img.get_width() != SUBTILE_SIZE or img.get_height() != SUBTILE_SIZE:
                img = pygame.transform.scale(img, (SUBTILE_SIZE, SUBTILE_SIZE))
            return img

        self.subtiles = {
            "P": load("grassy-plain.png"),
            "D": load("dirt.png"),
            "W": load("water.png"),
            "T": load("top-grass-dirt.png"),
            "B": load("bottom-grass-dirt.png"),
            "L": load("left-grass-dirt.png"),
            "R": load("right-grass-dirt.png"),
            "TL": load("top-left-grass-dirt.png"),
            "TR": load("top-right-grass-dirt.png"),
            "BL": load("bottom-left-grass-dirt.png"),
            "BR": load("bottom-right-grass-dirt.png"),
            "WT": load("top-grass-water.png"),
            "WB": load("bottom-grass-water.png"),
            "WL": load("left-grass-water.png"),
            "WR": load("right-grass-water.png"),
            "WTL": load("top-left-grass-water.png"),
            "WTR": load("top-right-grass-water.png"),
            "WBL": load("bottom-left-grass-water.png"),
            "WBR": load("bottom-right-grass-water.png"),
        }


    def _seed_map(self):
        self.w = GRID_W
        self.h = GRID_H
        self.tiles = [["PLAIN" for _ in range(self.w)] for _ in range(self.h)]
        self.paint_w = self.w * 2
        self.paint_h = self.h * 2

        rows = [
            "P P P P P P P P P P P P P P P P P P P P",
            "P TL T T T T T T T T T T T T T T T TR P",
            "P L D D D D D D D D D D D D D D D R P",
            "P L D D D D D D D D D D D D D D D R P",
            "P L D D D D D D D D D D D D D D D R P",
            "P BL B B B B B B B B B B B B B B B BR P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P WTL WT WT WT WT WT WT WT WT WT WT WT WT WT WT WT WTR P",
            "P WL W W W W W W W W W W W W W W W WR P",
            "P WL W W W W W W W W W W W W W W W WR P",
            "P WL W W W W W W W W W W W W W W W WR P",
            "P WBL WB WB WB WB WB WB WB WB WB WB WB WB WB WB WB WBR P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
        ]

        preset = [r.split() for r in rows]

        while len(preset) < self.paint_h:
            preset.append(["P"] * self.paint_w)
        preset = preset[:self.paint_h]

        for i in range(len(preset)):
            if len(preset[i]) < self.paint_w:
                preset[i] = preset[i] + (["P"] * (self.paint_w - len(preset[i])))
            else:
                preset[i] = preset[i][:self.paint_w]

        self.paint = preset

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
                r = self.cell_rect(x, y)
                px = x * 2
                py = y * 2

                k_tl = self.paint[py][px]
                k_tr = self.paint[py][px + 1]
                k_bl = self.paint[py + 1][px]
                k_br = self.paint[py + 1][px + 1]

                tl = self.subtiles.get(k_tl, self.subtiles["P"])
                tr = self.subtiles.get(k_tr, self.subtiles["P"])
                bl = self.subtiles.get(k_bl, self.subtiles["P"])
                br = self.subtiles.get(k_br, self.subtiles["P"])

                ox = r.left
                oy = r.top

                surf.blit(tl, (ox, oy))
                surf.blit(tr, (ox + SUBTILE_SIZE, oy))
                surf.blit(bl, (ox, oy + SUBTILE_SIZE))
                surf.blit(br, (ox + SUBTILE_SIZE, oy + SUBTILE_SIZE))

    def reachable_cells(self, start, move_points, blocked_cells):
        sx, sy = start
        dist = {(sx, sy): 0}
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