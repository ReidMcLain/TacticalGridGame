import pygame
from dataclasses import dataclass, field
from .constants import TILE_SIZE, TEAM_RED, TEAM_BLUE, BLACK, WHITE

UNIT_STATS = {
    "INFANTRY": {"max_hp": 8, "move": 4},
    "CAVALRY": {"max_hp": 10, "move": 6},
    "PIKEMAN": {"max_hp": 9, "move": 4},
    "CROSSBOW": {"max_hp": 7, "move": 4},
}

@dataclass
class Unit:
    team: int
    kind: str
    x: int
    y: int
    hp: int
    acted: bool = False
    has_attacked: bool = False
    move_left: int = 0

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
        self.move_left = self.move_points

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

    def damage(self):
        return max(1, self.hp)

    def begin_turn(self):
        self.acted = False
        self.has_attacked = False
        self.move_left = self.move_points

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
        color = TEAM_RED if self.team == 0 else TEAM_BLUE
        cx = int(self._px)
        cy = int(self._py)

        radius = TILE_SIZE // 3
        if self.acted:
            radius = TILE_SIZE // 4

        pygame.draw.circle(surf, color, (cx, cy), radius)
        pygame.draw.circle(surf, BLACK, (cx, cy), radius, 2)

        hp_txt = font_small.render(str(self.hp), True, WHITE)
        rect = hp_txt.get_rect(center=(cx, cy))
        surf.blit(hp_txt, rect)

def team_name(team):
    return "RED" if team == 0 else "BLUE"

def make_starting_units():
    units = []
    units.append(Unit(team=0, kind="INFANTRY", x=0, y=3, hp=UNIT_STATS["INFANTRY"]["max_hp"]))
    units.append(Unit(team=0, kind="CAVALRY", x=1, y=0, hp=UNIT_STATS["CAVALRY"]["max_hp"]))
    units.append(Unit(team=1, kind="INFANTRY", x=5, y=1, hp=UNIT_STATS["INFANTRY"]["max_hp"]))
    units.append(Unit(team=1, kind="CROSSBOW", x=4, y=5, hp=UNIT_STATS["CROSSBOW"]["max_hp"]))
    return units