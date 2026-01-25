import os
import pygame
from dataclasses import dataclass, field
from .constants import TILE_SIZE
import math

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

HP_Y_OFFSET_PX = 16
SPRITE_GAP_PX = 2

UNIT_DEFS = {
    "SOLDIER": {
        "max_hp": 100,
        "move": 4,
        "atk": 28,
        "armor": 6,
        "sprite": "soldier.png",
        "sprite_mode": "native",
        "anchor": "feet",
        "attack_sheet": "soldier-attack.png",
        "attack_frames": 2,
        "attack_range": 1,
        "target_height_px": int(TILE_SIZE * 0.65),
    },
    "ARCHER": {
        "max_hp": 100,
        "move": 4,
        "atk": 22,
        "armor": 2,
        "sprite": "Archer.png",
        "sprite_mode": "native",
        "anchor": "feet",
        "attack_sheet": "Archer-attack.png",
        "attack_frames": 3,
        "attack_range": 4,
        "target_height_px": int(TILE_SIZE * 0.65),
    },
}

_ASSET_CACHE = {}
_ARROW_BASE = None
_ARROW_ROT_CACHE = {}


def init_assets():
    def load_image(filename):
        path = os.path.join(_ASSETS_DIR, filename)
        return pygame.image.load(path).convert_alpha()

    def load_sprite(kind, filename, mode):
        img = load_image(filename)


        if mode == "tile":
            img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            return img

        target_h = UNIT_DEFS.get(kind, {}).get("target_height_px")
        if target_h and img.get_height() > 0 and img.get_height() != target_h:
            scale = target_h / img.get_height()
            new_w = max(1, int(round(img.get_width() * scale)))
            img = pygame.transform.scale(img, (new_w, int(target_h)))

        return img

    def load_arrow_base():
        global _ARROW_BASE

        img = load_image("arrow.png")
        print("arrow loaded", img.get_size())

        target_h = max(1, int(round(TILE_SIZE * 0.8)))
        if img.get_height() > 0 and img.get_height() != target_h:
            scale = target_h / img.get_height()
            new_w = max(1, int(round(img.get_width() * scale)))
            img = pygame.transform.scale(img, (new_w, int(target_h)))

        _ARROW_BASE = img
        _ARROW_ROT_CACHE.clear()

    def load_attack_sheet_scaled(kind, filename, frame_count):
        sheet = load_image(filename)
        sheet_w = sheet.get_width()
        sheet_h = sheet.get_height()

        vertical = (sheet_h % frame_count == 0) and (sheet_h >= sheet_w)
        if vertical:
            frame_w = sheet_w
            frame_h = sheet_h // frame_count
        else:
            frame_w = sheet_w // frame_count
            frame_h = sheet_h

        target_h = UNIT_DEFS.get(kind, {}).get("target_height_px")
        if not target_h:
            target_h = frame_h

        frames = []
        for i in range(frame_count):
            if vertical:
                src = pygame.Rect(0, i * frame_h, frame_w, frame_h)
            else:
                src = pygame.Rect(i * frame_w, 0, frame_w, frame_h)

            frame = sheet.subsurface(src).copy()
            scale = target_h / frame_h
            new_w = max(1, int(round(frame_w * scale)))
            frame = pygame.transform.scale(frame, (new_w, int(target_h)))
            frames.append(frame)

        return frames

    def make_done_variant(img):
        done = img.copy()
        done.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGB_MULT)
        done.set_alpha(185)
        return done

    _ASSET_CACHE.clear()

    load_arrow_base()

    for kind, d in UNIT_DEFS.items():
        base = load_sprite(kind, d["sprite"], d.get("sprite_mode", "native"))

        flipped = pygame.transform.flip(base, True, False)

        entry = {
            "base": base,
            "flipped": flipped,
            "done": make_done_variant(base),
            "done_flipped": make_done_variant(flipped),
            "attack": None,
            "attack_flipped": None,
            "attack_done": None,
            "attack_done_flipped": None,
            "anchor": d.get("anchor", "feet"),
        }

        sheet = d.get("attack_sheet")
        frame_count = d.get("attack_frames", 0)
        if sheet and frame_count:
            frames = load_attack_sheet_scaled(kind, sheet, frame_count)
            frames_flipped = [pygame.transform.flip(f, True, False) for f in frames]
            entry["attack"] = frames
            entry["attack_flipped"] = frames_flipped
            entry["attack_done"] = [make_done_variant(f) for f in frames]
            entry["attack_done_flipped"] = [make_done_variant(f) for f in frames_flipped]

        _ASSET_CACHE[kind] = entry

def _get_asset_entry(kind):
    return _ASSET_CACHE.get(kind)

def get_arrow_sprite(dx, dy):
    if _ARROW_BASE is None:
        return None

    angle = -math.degrees(math.atan2(dy, dx))

    key = int(round(angle))
    if key not in _ARROW_ROT_CACHE:
        _ARROW_ROT_CACHE[key] = pygame.transform.rotate(_ARROW_BASE, key)

    return _ARROW_ROT_CACHE[key]

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
        return UNIT_DEFS[self.kind]["max_hp"]

    @property
    def move_points(self):
        return UNIT_DEFS[self.kind]["move"]
    
    @property
    def attack_range(self):
        return UNIT_DEFS[self.kind].get("attack_range", 1)
    
    @property
    def atk(self):
        return UNIT_DEFS[self.kind].get("atk", 20)

    @property
    def armor(self):
        return UNIT_DEFS[self.kind].get("armor", 0)

    @property
    def attack_range(self):
        return UNIT_DEFS[self.kind].get("attack_range", 1)

    def pos(self):
        return (self.x, self.y)

    def is_alive(self):
        return self.hp > 0

    def _cell_center(self, x, y):
        return (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)

    def start_attack_anim(self):
        entry = _get_asset_entry(self.kind)
        if not entry:
            return
        frames = entry["attack"]
        if not frames:
            return
        self.attacking = True
        self._attack_frame_i = 0
        self._attack_accum_ms = 0

    def update_attack(self, dt_ms):
        if not self.attacking:
            return

        entry = _get_asset_entry(self.kind)
        if not entry:
            self.attacking = False
            self._attack_frame_i = 0
            return

        frames = entry["attack"]
        if not frames:
            self.attacking = False
            self._attack_frame_i = 0
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
        entry = _get_asset_entry(self.kind)
        if not entry:
            return

        use_done = (self.acted and self.team == active_team)

        if self.attacking and entry["attack"]:
            frames = entry["attack_flipped"] if is_enemy else entry["attack"]
            i = min(self._attack_frame_i, len(frames) - 1)
            if use_done:
                frames_done = entry["attack_done_flipped"] if is_enemy else entry["attack_done"]
                img = frames_done[i]
            else:
                img = frames[i]
        else:
            base = entry["flipped"] if is_enemy else entry["base"]
            if use_done:
                img = entry["done_flipped"] if is_enemy else entry["done"]
            else:
                img = base

        surf.blit(
            img,
            img.get_rect(
                midbottom=(cx, cy + TILE_SIZE // 2 - (HP_Y_OFFSET_PX + SPRITE_GAP_PX))
            ),
        )

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
        Unit(team=0, kind="ARCHER", x=0, y=4, hp=100),
        Unit(team=0, kind="ARCHER", x=0, y=5, hp=100),
        Unit(team=0, kind="ARCHER", x=0, y=6, hp=100),
        Unit(team=0, kind="SOLDIER", x=1, y=4, hp=100),
        Unit(team=0, kind="SOLDIER", x=1, y=5, hp=100),
        Unit(team=0, kind="SOLDIER", x=1, y=6, hp=100),
        Unit(team=1, kind="SOLDIER", x=8, y=4, hp=100),
        Unit(team=1, kind="SOLDIER", x=8, y=5, hp=100),
        Unit(team=1, kind="SOLDIER", x=8, y=6, hp=100),
        Unit(team=1, kind="ARCHER", x=9, y=4, hp=100),
        Unit(team=1, kind="ARCHER", x=9, y=5, hp=100),
        Unit(team=1, kind="ARCHER", x=9, y=6, hp=100),
    ]