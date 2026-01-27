import os

GRID_W = 10
GRID_H = 10
TILE_SIZE = 64
SUBTILE_SIZE = TILE_SIZE // 2

SCREEN_W = GRID_W * TILE_SIZE
UI_H = 120
SCREEN_H = GRID_H * TILE_SIZE + UI_H

FPS = 60

WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
GRAY = (110, 110, 110)
DARK = (35, 35, 35)

TEAM_RED = (220, 70, 70)
TEAM_GREEN = (70, 220, 120)
TEAM_BLUE = TEAM_GREEN

HIGHLIGHT_MOVE = (245, 245, 120)
HIGHLIGHT_ATTACK = (255, 140, 140)
HIGHLIGHT_SELECT = (255, 255, 255)

TILES = {
    "PLAIN": {"move_cost": 1, "def_bonus": 0},
    "DIRT": {"move_cost": 1, "def_bonus": 0},
    "FOREST": {"move_cost": 2, "def_bonus": 1},
    "HILL": {"move_cost": 2, "def_bonus": 2},
    "WATER": {"move_cost": 999, "def_bonus": 0},
}

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")