import os

GRID_W = 6
GRID_H = 6
TILE_SIZE = 96

SCREEN_W = GRID_W * TILE_SIZE
UI_H = 120
SCREEN_H = GRID_H * TILE_SIZE + UI_H

FPS = 60

WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
GRAY = (110, 110, 110)
DARK = (35, 35, 35)

TEAM_RED = (220, 70, 70)
TEAM_BLUE = (80, 140, 240)

TILE_COLORS = {
    "PLAIN": (86, 140, 86),
    "FOREST": (46, 100, 60),
    "HILL": (130, 120, 90),
    "WATER": (50, 90, 150),
}

HIGHLIGHT_MOVE = (245, 245, 120)
HIGHLIGHT_ATTACK = (255, 140, 140)
HIGHLIGHT_SELECT = (255, 255, 255)

TILES = {
    "PLAIN": {"move_cost": 1, "def_bonus": 0},
    "FOREST": {"move_cost": 2, "def_bonus": 1},
    "HILL": {"move_cost": 2, "def_bonus": 2},
    "WATER": {"move_cost": 999, "def_bonus": 0},
}

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")