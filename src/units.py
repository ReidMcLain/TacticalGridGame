import os
import pygame
from dataclasses import dataclass, field
from .constants import TILE_SIZE

UNIT_STATS = {
    "FOOTSOLDIER": {"max_hp": 100, "move": 4},
}

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

_SPRITES = {
    "FOOTSOLDIER": None,
}

_SPRITES_FLIPPED = {
    "FOOTSOLDIER": None,
}

_SPRITES_DONE = {
    "FOOTSOLDIER": None,
}

_SPRITES_DONE_FLIPPED = {
    "FOOTSOLDIER": None,
}

_ATTACK_FRAMES = {
    "FOOTSOLDIER": None,
}

_ATTACK_FRAMES_FLIPPED = {
    "FOOTSOLDIER": None,
}

_ATTACK_FRAMES_DONE = {
    "FOOTSOLDIER": None,
}

_ATTACK_FRAMES_DONE_FLIPPED = {
    "FOOTSOLDIER": None,
}


def init_assets():
    def load_scaled(filename):
        path = os.path.join(_ASSETS_DIR, filename)
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        return img

    def load_attack_sheet_2frames_keep_height(filename):
        path = os.path.join(_ASSETS_DIR, filename)
        sheet = pygame.image.load(path).convert_alpha()

        sheet_w = sheet.get_width()
        sheet_h = sheet.get_height()

        frame_count = 2
        frame_w = sheet_w // frame_count
        frame_h = sheet_h

        frames = []
        for i in range(frame_count):
            src = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frame = sheet.subsurface(src).copy()
            scale = TILE_SIZE / frame_h
            new_w = max(1, int(round(frame_w * scale)))
            frame = pygame.transform.scale(frame, (new_w, TILE_SIZE))
            frames.append(frame)

        return frames

    def make_done_variant(img):
        done = img.copy()
        done.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGB_MULT)
        done.set_alpha(185)
        return done

    _SPRITES["FOOTSOLDIER"] = load_scaled("footsoldier.png")
    _SPRITES_FLIPPED["FOOTSOLDIER"] = pygame.transform.flip(
        _SPRITES["FOOTSOLDIER"], True, False
    )

    _SPRITES_DONE["FOOTSOLDIER"] = make_done_variant(_SPRITES["FOOTSOLDIER"])
    _SPRITES_DONE_FLIPPED["FOOTSOLDIER"] = make_done_variant(_SPRITES_FLIPPED["FOOTSOLDIER"])

    _ATTACK_FRAMES["FOOTSOLDIER"] = load_attack_sheet_2frames_keep_height(
        "footsoldier-attack.png"
    )
    _ATTACK_FRAMES_FLIPPED["FOOTSOLDIER"] = [
        pygame.transform.flip(f, True, False)
        for f in _ATTACK_FRAMES["FOOTSOLDIER"]
    ]

    _ATTACK_FRAMES_DONE["FOOTSOLDIER"] = [make_done_variant(f) for f in _ATTACK_FRAMES["FOOTSOLDIER"]]
    _ATTACK_FRAMES_DONE_FLIPPED["FOOTSOLDIER"] = [make_done_variant(f) for f in _ATTACK_FRAMES_FLIPPED["FOOTSOLDIER"]]


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

    attacking: bool = False
    _attack_frame_i: int = 0
    _attack_accum_ms: int = 0
    _attack_frame_ms: int = 140

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

    def start_attack_anim(self):
        frames = _ATTACK_FRAMES.get(self.kind)
        if not frames:
            return
        self.attacking = True
        self._attack_frame_i = 0
        self._attack_accum_ms = 0

    def update_attack(self, dt_ms):
        if not self.attacking:
            return

        frames = _ATTACK_FRAMES.get(self.kind)
        if not frames:
            self.attacking = False
            return

        self._attack_accum_ms += int(dt_ms)

        while self._attack_accum_ms >= self._attack_frame_ms:
            self._attack_accum_ms -= self._attack_frame_ms
            self._attack_frame_i += 1

            if self._attack_frame_i >= len(frames):
                self.attacking = False
                self._attack_frame_i = 0
                break

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

    def draw(self, surf, font_small, active_team):
        cx = int(self._px)
        cy = int(self._py)

        is_enemy = (self.team == 1)

        if self.attacking:
            frames = (_ATTACK_FRAMES_FLIPPED if is_enemy else _ATTACK_FRAMES)[self.kind]
            base = frames[min(self._attack_frame_i, len(frames) - 1)]
        else:
            base = (_SPRITES_FLIPPED if is_enemy else _SPRITES)[self.kind]

        img = base
        if self.acted and self.team == active_team:
            img = base.copy()
            img.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)

        surf.blit(img, img.get_rect(center=(cx, cy)))

        green = (0, 220, 0)
        red = (235, 40, 40)
        hp_color = red if is_enemy else green

        hp_txt = font_small.render(str(self.hp), True, hp_color)
        hp_rect = hp_txt.get_rect(center=(cx, cy + TILE_SIZE // 2 - 8))
        surf.blit(hp_txt, hp_rect)

def team_name(team):
    return "GREEN" if team == 0 else "RED"


def make_starting_units():
    return [
        Unit(team=0, kind="FOOTSOLDIER", x=0, y=4, hp=100),
        Unit(team=0, kind="FOOTSOLDIER", x=0, y=5, hp=100),
        Unit(team=0, kind="FOOTSOLDIER", x=0, y=6, hp=100),
        Unit(team=0, kind="FOOTSOLDIER", x=1, y=4, hp=100),
        Unit(team=0, kind="FOOTSOLDIER", x=1, y=5, hp=100),
        Unit(team=0, kind="FOOTSOLDIER", x=1, y=6, hp=100),
        Unit(team=1, kind="FOOTSOLDIER", x=18, y=4, hp=100),
        Unit(team=1, kind="FOOTSOLDIER", x=18, y=5, hp=100),
        Unit(team=1, kind="FOOTSOLDIER", x=18, y=6, hp=100),
        Unit(team=1, kind="FOOTSOLDIER", x=19, y=4, hp=100),
        Unit(team=1, kind="FOOTSOLDIER", x=19, y=5, hp=100),
        Unit(team=1, kind="FOOTSOLDIER", x=19, y=6, hp=100),
    ]