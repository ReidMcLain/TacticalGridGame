import pygame
from .grid import Grid
from .units import make_starting_units, team_name
from .constants import (
    SCREEN_W, SCREEN_H, UI_H, TILE_SIZE,
    BLACK, WHITE, HIGHLIGHT_MOVE, HIGHLIGHT_ATTACK, HIGHLIGHT_SELECT
)

class Game:
    def __init__(self, ui):
        self.ui = ui
        self.grid = Grid()
        self.units = make_starting_units()
        self.turn_team = 0
        self.selected = None
        self.reachable = set()
        self.attackables = set()
        self.winner = None

    def units_alive(self, team):
        return [u for u in self.units if u.team == team and u.is_alive()]

    def unit_at(self, x, y):
        for u in self.units:
            if u.is_alive() and u.x == x and u.y == y:
                return u
        return None

    def occupied_cells(self):
        return {(u.x, u.y) for u in self.units if u.is_alive()}

    def enemies_of(self, unit):
        return [u for u in self.units if u.is_alive() and u.team != unit.team]

    def allies_of(self, unit):
        return [u for u in self.units if u.is_alive() and u.team == unit.team]

    def end_turn(self):
        self.selected = None
        self.reachable = set()
        self.attackables = set()

        self.turn_team = 1 - self.turn_team
        for u in self.units:
            if u.team == self.turn_team:
                u.acted = False

    def compute_reachable_and_attackables(self, unit):
        blocked = self.occupied_cells() - {unit.pos()}
        self.reachable = self.grid.reachable_cells(unit.pos(), unit.move_points, blocked)

        attackables = set()
        for x, y in self.reachable:
            for nx, ny in self.grid.neighbors4(x, y):
                enemy = self.unit_at(nx, ny)
                if enemy and enemy.team != unit.team:
                    attackables.add((nx, ny))
        self.attackables = attackables

    def try_select(self, cell):
        x, y = cell
        u = self.unit_at(x, y)
        if not u:
            self.selected = None
            self.reachable = set()
            self.attackables = set()
            return

        if u.team != self.turn_team:
            return

        if u.acted:
            return

        self.selected = u
        self.compute_reachable_and_attackables(u)

    def try_move_or_attack(self, cell):
        if not self.selected:
            return

        x, y = cell
        if (x, y) in self.attackables:
            self.attack(self.selected, self.unit_at(x, y))
            return

        if (x, y) in self.reachable and self.unit_at(x, y) is None:
            self.selected.x = x
            self.selected.y = y
            self.compute_reachable_and_attackables(self.selected)
            return

        if self.unit_at(x, y) == self.selected:
            self.selected = None
            self.reachable = set()
            self.attackables = set()

    def attack(self, attacker, defender):
        if not attacker or not defender:
            return
        if attacker.acted:
            return

        base = attacker.damage()
        def_bonus = self.grid.def_bonus(defender.x, defender.y)
        dmg = max(1, base - def_bonus)

        defender.hp -= dmg
        attacker.acted = True
        self.selected = None
        self.reachable = set()
        self.attackables = set()

        if not defender.is_alive():
            pass

        self.check_win()

    def check_win(self):
        red = len(self.units_alive(0))
        blue = len(self.units_alive(1))
        if red == 0:
            self.winner = 1
        elif blue == 0:
            self.winner = 0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE and self.winner is None:
                self.end_turn()

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            cell = self.grid.cell_from_pixel(*e.pos)
            if cell is None:
                return
            if self.winner is not None:
                return

            if self.selected is None:
                self.try_select(cell)
            else:
                self.try_move_or_attack(cell)

    def draw_highlights(self, surf):
        for x, y in self.reachable:
            r = self.grid.cell_rect(x, y)
            overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            overlay.fill((*HIGHLIGHT_MOVE, 70))
            surf.blit(overlay, r.topleft)

        for x, y in self.attackables:
            r = self.grid.cell_rect(x, y)
            overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            overlay.fill((*HIGHLIGHT_ATTACK, 90))
            surf.blit(overlay, r.topleft)

        if self.selected:
            x, y = self.selected.pos()
            r = self.grid.cell_rect(x, y)
            pygame.draw.rect(surf, HIGHLIGHT_SELECT, r, 3)

    def draw(self, surf):
        surf.fill(BLACK)
        self.grid.draw(surf)
        self.draw_highlights(surf)

        for u in self.units:
            if u.is_alive():
                u.draw(surf, self.ui.small)

        lines = []
        if self.winner is None:
            lines.append(f"Turn: {team_name(self.turn_team)}   (SPACE = end turn)")
            if self.selected:
                lines.append(f"Selected: {self.selected.kind} HP={self.selected.hp} Move={self.selected.move_points}  | Click tile to move, red highlight to attack")
            else:
                lines.append("Click your unit to select. Move by clicking reachable tiles.")
            lines.append("Terrain: FOREST/HILL reduce damage taken (def bonus). WATER is impassable.")
        else:
            lines.append(f"{team_name(self.winner)} wins!")
            lines.append("Restart the program to play again.")
            lines.append("Next: we’ll add turn-order lock-in + unit list + better action rules.")

        self.ui.draw_panel(surf, lines)