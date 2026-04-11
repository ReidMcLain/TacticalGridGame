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

        self.walls = [
            [{"top": False, "right": False, "bottom": False, "left": False} for _ in range(self.w)]
            for _ in range(self.h)
        ]

        self._seed_map()
        self._sync_gameplay_tiles_from_paint()
        self._sync_walls_from_paint()
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
            "HT": load("top-hill.png"),
            "HB": load("bottom-hill.png"),
            "HL": load("left-hill.png"),
            "HR": load("right-hill.png"),
            "HTL": load("top-left-hill.png"),
            "HTR": load("top-right-hill.png"),
            "HBL": load("bottom-left-hill.png"),
            "HBR": load("bottom-right-hill.png"),
        }

    def _seed_map(self):
        rows = [
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P TL T T T T T T T T T T T T T T TR P P",
            "P P L D D D D D D D D D D D D D D R P P",
            "P P L D D D D D D D D D D D D D D R P P",
            "P P BL B B B B B B B B B B B B B B BR P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P WTL WT WT WT WT WT WT WT WT WT WT WT WT WT WT WTR P P",
            "P P WL W W W W W W W W W W W W W W WR P P",
            "P P WL W W W W W W W W W W W W W W WR P P",
            "P P WBL WB WB WB WB WB WB WB WB WB WB WB WB WB WB WBR P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P HTL HT HT HT HT HT HT HT HT HT HT HT HT HT HT HTR P P",
            "P P HL P P P P P P P P P P P P P P HR P P",
            "P P P P P P P P P P P P P P P P P HR P P",
            "P P HB HB HB HB HB HB HB HB HB HB HB HB HB HB HB HBR P P",
            "P P P P P P P P P P P P P P P P P P P P",
            "P P P P P P P P P P P P P P P P P P P P",
        ]

        preset = [row.split() for row in rows]

        while len(preset) < self.paint_h:
            preset.append(["P"] * self.paint_w)

        preset = preset[:self.paint_h]

        for i in range(len(preset)):
            if len(preset[i]) < self.paint_w:
                preset[i] += ["P"] * (self.paint_w - len(preset[i]))
            else:
                preset[i] = preset[i][:self.paint_w]

        self.paint = preset

    def _sync_gameplay_tiles_from_paint(self):
        water_tokens = {"W", "WT", "WB", "WL", "WR", "WTL", "WTR", "WBL", "WBR"}

        self.tiles = [["PLAIN" for _ in range(self.w)] for _ in range(self.h)]

        for y in range(self.h):
            for x in range(self.w):
                px = x * 2
                py = y * 2

                quad = {
                    self.paint[py][px],
                    self.paint[py][px + 1],
                    self.paint[py + 1][px],
                    self.paint[py + 1][px + 1],
                }

                if quad.issubset(water_tokens):
                    self.tiles[y][x] = "WATER"

    def _sync_walls_from_paint(self):
        self.walls = [
            [{"top": False, "right": False, "bottom": False, "left": False} for _ in range(self.w)]
            for _ in range(self.h)
        ]

        hill_top_tokens = {"HT", "HTL", "HTR"}
        hill_bottom_tokens = {"HB", "HBL", "HBR"}
        hill_left_tokens = {"HL", "HTL", "HBL"}
        hill_right_tokens = {"HR", "HTR", "HBR"}

        for y in range(self.h):
            for x in range(self.w):
                px = x * 2
                py = y * 2

                quad = [
                    self.paint[py][px],
                    self.paint[py][px + 1],
                    self.paint[py + 1][px],
                    self.paint[py + 1][px + 1],
                ]

                wall = self.walls[y][x]

                if any(token in hill_top_tokens for token in quad):
                    wall["top"] = True

                if any(token in hill_bottom_tokens for token in quad):
                    wall["bottom"] = True

                if any(token in hill_left_tokens for token in quad):
                    wall["left"] = True

                if any(token in hill_right_tokens for token in quad):
                    wall["right"] = True

    def in_bounds(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def tile_type(self, x, y):
        return self.tiles[y][x]

    def move_cost(self, x, y):
        return TILES[self.tile_type(x, y)]["move_cost"]

    def def_bonus(self, x, y):
        return TILES[self.tile_type(x, y)]["def_bonus"]

    def cell_from_pixel(self, px, py):
        if py >= self.h * TILE_SIZE:
            return None

        x = px // TILE_SIZE
        y = py // TILE_SIZE

        if not self.in_bounds(x, y):
            return None

        return (x, y)

    def cell_rect(self, x, y):
        return pygame.Rect(
            x * TILE_SIZE,
            y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE
        )

    def neighbors4(self, x, y):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy

            if self.in_bounds(nx, ny):
                yield (nx, ny)

    def edge_blocked(self, x, y, nx, ny):
        if nx == x and ny == y - 1:
            return self.walls[y][x]["top"] or self.walls[ny][nx]["bottom"]

        if nx == x and ny == y + 1:
            return self.walls[y][x]["bottom"] or self.walls[ny][nx]["top"]

        if nx == x - 1 and ny == y:
            return self.walls[y][x]["left"] or self.walls[ny][nx]["right"]

        if nx == x + 1 and ny == y:
            return self.walls[y][x]["right"] or self.walls[ny][nx]["left"]

        return False

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

                surf.blit(tl, (r.left, r.top))
                surf.blit(tr, (r.left + SUBTILE_SIZE, r.top))
                surf.blit(bl, (r.left, r.top + SUBTILE_SIZE))
                surf.blit(br, (r.left + SUBTILE_SIZE, r.top + SUBTILE_SIZE))

    def reachable_cells(self, start, move_points, blocked_cells):
        sx, sy = start

        dist = {(sx, sy): 0}
        q = deque([(sx, sy)])

        while q:
            x, y = q.popleft()

            for nx, ny in self.neighbors4(x, y):
                if self.edge_blocked(x, y, nx, ny):
                    continue

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