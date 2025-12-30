import os
import pygame
from dataclasses import dataclass, field
from .constants import TILE_SIZE, WHITE, BLACK, TEAM_RED, TEAM_BLUE

# --- GAME UNITS (v0.02) ---
UNIT_STATS = {
    "POTION": {"max_hp": 100, "move": 4},
    "SKULL": {"max_hp": 100, "move": 4},
}

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

# sprite cache (loaded AFTER display init)
_SPRITES = {
    "POTION": None,
    "SKULL": None,
}

def init_assets():
    """
    Call this AFTER pygame.display.set_mode(...)
    """
    def load(filename):
        path = os.path.join(_ASSETS_DIR, filename)
        img = pygame.image.load(path).convert_alpha()
        # crisp pixel scaling (no blur)
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        return img

    _SPRITES["POTION"] = load("Potion.png")
    _SPRITES["SKULL"] = load("Skull.png")

@dataclass
class Unit:
    team: int
    kind: str
    x: int
    y: int
    hp: int
    acted: bool = False

    moving: bool = False
    _path: list = field(default_factory=list)
    _px: float = 0.0
    _py: float = 0.0
    _target_px: float = 0.0
    _target_py: float = 0.0

    def __post_init__(self):
        self._px = float(self.x * TILE_SIZE + TILE_SIZE // 2)
        self._py = float(self.y * TILE_SIZE + TILE_SIZE // 2)
        self._target_px = self._px
        self._target_py = self._py

    @property
    def max_hp(self):
        return UNIT_STATS[self.kind]["max_hp"]

    @property
    def move_points(self):
        return UNIT_STATS[self.kind]["move"]

    def pos(self):
        return (self.x, self.y)

    def is_alive(self):
        return self.hp > 0

    def _cell_center(self, x, y):
        return (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)

    def start_path(self, path_cells):
        if not path_cells:
            return
        self._path = list(path_cells)
        self.moving = True
        nx, ny = self._path[0]
        tx, ty = self._cell_center(nx, ny)
        self._target_px = float(tx)
        self._target_py = float(ty)

    def update(self, dt_ms):
        if not self.moving:
            return

        speed_px_per_ms = 0.45
        step = speed_px_per_ms * dt_ms

        dx = self._target_px - self._px
        dy = self._target_py - self._py
        dist = (dx * dx + dy * dy) ** 0.5

        if dist <= step or dist == 0:
            self._px = self._target_px
            self._py = self._target_py

            nx, ny = self._path.pop(0)
            self.x, self.y = nx, ny

            if not self._path:
                self.moving = False
                return

            nx, ny = self._path[0]
            tx, ty = self._cell_center(nx, ny)
            self._target_px = float(tx)
            self._target_py = float(ty)
            return

        self._px += (dx / dist) * step
        self._py += (dy / dist) * step

    def draw(self, surf, font_small):
        cx = int(self._px)
        cy = int(self._py)

        img = _SPRITES.get(self.kind)
        if img is not None:
            surf.blit(img, img.get_rect(center=(cx, cy)))
        else:
            # if assets weren't initialized, show a simple fallback (not circles)
            color = TEAM_RED if self.team == 0 else TEAM_BLUE
            r = pygame.Rect(0, 0, TILE_SIZE - 20, TILE_SIZE - 20)
            r.center = (cx, cy)
            pygame.draw.rect(surf, color, r)

        # HP label ABOVE sprite
        hp_txt = font_small.render(str(self.hp), True, WHITE)
        hp_rect = hp_txt.get_rect(center=(cx, cy - TILE_SIZE // 2 + 12))
        outline = hp_rect.inflate(6, 4)
        pygame.draw.rect(surf, BLACK, outline, border_radius=4)
        surf.blit(hp_txt, hp_rect)

def team_name(team):
    return "RED" if team == 0 else "BLUE"

def make_starting_units():
    units = []

    # RED: 2 potions
    units.append(Unit(team=0, kind="POTION", x=0, y=3, hp=UNIT_STATS["POTION"]["max_hp"]))
    units.append(Unit(team=0, kind="POTION", x=1, y=0, hp=UNIT_STATS["POTION"]["max_hp"]))

    # BLUE: 2 skulls
    units.append(Unit(team=1, kind="SKULL", x=5, y=1, hp=UNIT_STATS["SKULL"]["max_hp"]))
    units.append(Unit(team=1, kind="SKULL", x=4, y=5, hp=UNIT_STATS["SKULL"]["max_hp"]))

    return units