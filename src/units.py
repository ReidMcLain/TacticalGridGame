import pygame
from dataclasses import dataclass
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

    def draw(self, surf, font_small):
        cx = self.x * TILE_SIZE + TILE_SIZE // 2
        cy = self.y * TILE_SIZE + TILE_SIZE // 2
        color = TEAM_RED if self.team == 0 else TEAM_BLUE

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
    units.append(Unit(team=0, kind="INFANTRY", x=0, y=0, hp=UNIT_STATS["INFANTRY"]["max_hp"]))
    units.append(Unit(team=0, kind="CAVALRY", x=1, y=0, hp=UNIT_STATS["CAVALRY"]["max_hp"]))
    units.append(Unit(team=1, kind="INFANTRY", x=5, y=5, hp=UNIT_STATS["INFANTRY"]["max_hp"]))
    units.append(Unit(team=1, kind="CROSSBOW", x=4, y=5, hp=UNIT_STATS["CROSSBOW"]["max_hp"]))
    return units