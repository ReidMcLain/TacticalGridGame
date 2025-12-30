import pygame
from collections import deque
from .grid import Grid
from .units import make_starting_units, team_name
from .constants import TILE_SIZE, BLACK, HIGHLIGHT_MOVE, HIGHLIGHT_ATTACK, HIGHLIGHT_SELECT

AI_TEAM = 1

class Game:
    def __init__(self, ui):
        self.ui = ui
        self.grid = Grid()
        self.units = make_starting_units()
        self.turn_team = 0
        self.selected = None
        self.reachable = set()
        self.attackables = set()
        self.animating_unit = None
        self.winner = None

        self.in_ai_turn = False

        self.log_lines = deque(maxlen=4)
        self._log(f"Game start. Turn: {team_name(self.turn_team)}")

    def _log(self, msg):
        print(msg)
        self.log_lines.appendleft(msg)

    def units_alive(self, team):
        return [u for u in self.units if u.team == team and u.is_alive()]

    def unit_at(self, x, y):
        for u in self.units:
            if u.is_alive() and u.x == x and u.y == y:
                return u
        return None

    def occupied_cells(self):
        return {(u.x, u.y) for u in self.units if u.is_alive()}

    def clear_selection(self):
        self.selected = None
        self.reachable = set()
        self.attackables = set()

    def ensure_flags(self, unit):
        if not hasattr(unit, "has_moved"):
            unit.has_moved = False

    def find_path(self, start, goal):
        q = deque([start])
        came_from = {start: None}
        blocked = self.occupied_cells() - {start}

        while q:
            x, y = q.popleft()
            if (x, y) == goal:
                break
            for nx, ny in self.grid.neighbors4(x, y):
                if (nx, ny) in came_from:
                    continue
                if self.grid.move_cost(nx, ny) >= 999:
                    continue
                if (nx, ny) in blocked:
                    continue
                came_from[(nx, ny)] = (x, y)
                q.append((nx, ny))

        if goal not in came_from:
            return []

        path = []
        cur = goal
        while cur != start:
            path.append(cur)
            cur = came_from[cur]
        path.reverse()
        return path

    def compute_reachable_and_attackables(self, unit):
        self.ensure_flags(unit)

        if unit.has_moved:
            self.reachable = set()
        else:
            blocked = self.occupied_cells() - {unit.pos()}
            self.reachable = self.grid.reachable_cells(unit.pos(), unit.move_points, blocked)

        self.attackables = set()
        ux, uy = unit.pos()
        for nx, ny in self.grid.neighbors4(ux, uy):
            enemy = self.unit_at(nx, ny)
            if enemy and enemy.team != unit.team:
                self.attackables.add((nx, ny))

    def check_win(self):
        if not self.units_alive(0):
            self.winner = 1
        elif not self.units_alive(1):
            self.winner = 0

        if self.winner is not None:
            self._log(f"{team_name(self.winner)} wins!")

    def check_auto_end_turn(self):
        for u in self.units:
            if u.team == self.turn_team and u.is_alive() and not u.acted:
                return
        self.end_turn()

    def finish_unit_turn(self, unit):
        self.ensure_flags(unit)
        unit.acted = True
        unit.has_moved = False
        self.clear_selection()

        self.check_win()
        if self.winner is not None:
            return

        # IMPORTANT: during AI processing, do NOT auto-end turns here.
        if not self.in_ai_turn:
            self.check_auto_end_turn()

    def end_turn(self):
        self.clear_selection()
        self.turn_team = 1 - self.turn_team

        for u in self.units:
            if u.team == self.turn_team:
                self.ensure_flags(u)
                u.acted = False
                u.has_moved = False

        self._log(f"Turn: {team_name(self.turn_team)}")

        if self.turn_team == AI_TEAM and self.winner is None:
            self.run_ai_turn()

    def attack(self, attacker, defender):
        if not attacker or not defender:
            return
        if attacker.acted:
            return

        before = defender.hp
        base = int(attacker.hp * 0.40)  # 40% of CURRENT hp (shared hp/attack pool idea)
        dmg = max(1, base - self.grid.def_bonus(defender.x, defender.y))

        defender.hp -= dmg
        if defender.hp < 0:
            defender.hp = 0

        self._log(
            f"{team_name(attacker.team)} {attacker.kind} attacked "
            f"{team_name(defender.team)} {defender.kind} for {dmg} ({before}->{defender.hp})"
        )

        if defender.hp <= 0:
            self._log(f"{team_name(defender.team)} {defender.kind} died.")

        self.finish_unit_turn(attacker)

    def try_select(self, cell):
        u = self.unit_at(*cell)
        if not u:
            self.clear_selection()
            return

        if u.team != self.turn_team or u.acted:
            return

        if self.selected == u:
            self.clear_selection()
            return

        self.ensure_flags(u)
        self.selected = u
        self.compute_reachable_and_attackables(u)

    def try_move_or_attack(self, cell):
        if not self.selected:
            return
        if self.animating_unit:
            return

        self.ensure_flags(self.selected)

        if cell in self.attackables:
            self.attack(self.selected, self.unit_at(*cell))
            return

        if self.selected.has_moved:
            return

        if cell in self.reachable and self.unit_at(*cell) is None:
            path = self.find_path(self.selected.pos(), cell)
            if path:
                self.selected.start_path(path)
                self.selected.has_moved = True
                self.animating_unit = self.selected

    def handle_event(self, e):
        if self.turn_team == AI_TEAM or self.animating_unit or self.winner is not None:
            return

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                self.end_turn()
            if e.key == pygame.K_w and self.selected:
                self.finish_unit_turn(self.selected)

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            cell = self.grid.cell_from_pixel(*e.pos)
            if cell is None:
                return
            if self.selected:
                self.try_move_or_attack(cell)
            else:
                self.try_select(cell)

    def run_ai_turn(self):
        if self.winner is not None:
            return

        self.in_ai_turn = True

        for unit in self.units_alive(AI_TEAM):
            self.ensure_flags(unit)
            if unit.acted or not unit.is_alive():
                continue

            self.selected = unit
            self.compute_reachable_and_attackables(unit)

            if self.attackables:
                self.attack(unit, self.unit_at(*next(iter(self.attackables))))
                if self.winner is not None:
                    self.in_ai_turn = False
                    return
                continue

            enemies = self.units_alive(0)
            if not enemies:
                self.finish_unit_turn(unit)
                if self.winner is not None:
                    self.in_ai_turn = False
                    return
                continue

            best_cell = None
            best_dist = 10**9
            for e in enemies:
                for c in (self.reachable if self.reachable else {unit.pos()}):
                    d = abs(e.x - c[0]) + abs(e.y - c[1])
                    if d < best_dist:
                        best_dist = d
                        best_cell = c

            if best_cell and best_cell != unit.pos():
                path = self.find_path(unit.pos(), best_cell)
                if path:
                    unit.start_path(path)
                    unit.has_moved = True
                    self.animating_unit = unit
                    # AI will resume after movement finishes in update()
                    return

            self.finish_unit_turn(unit)
            if self.winner is not None:
                self.in_ai_turn = False
                return

        self.in_ai_turn = False
        self.end_turn()

    def ai_after_move(self, unit):
        self.selected = unit
        self.compute_reachable_and_attackables(unit)

        if self.attackables:
            self.attack(unit, self.unit_at(*next(iter(self.attackables))))
            return

        self.finish_unit_turn(unit)

    def update(self, dt_ms):
        if self.animating_unit:
            self.animating_unit.update(dt_ms)
            if not self.animating_unit.moving:
                moved_unit = self.animating_unit
                self.animating_unit = None

                if moved_unit.team == AI_TEAM:
                    self.ai_after_move(moved_unit)
                    if self.winner is not None:
                        self.in_ai_turn = False
                        return
                    # continue AI loop after its move resolves
                    self.run_ai_turn()
                    return

                self.selected = moved_unit
                self.compute_reachable_and_attackables(moved_unit)

                if not self.attackables:
                    self.finish_unit_turn(moved_unit)

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
            r = self.grid.cell_rect(*self.selected.pos())
            pygame.draw.rect(surf, HIGHLIGHT_SELECT, r, 3)

    def draw(self, surf):
        surf.fill(BLACK)
        self.grid.draw(surf)
        self.draw_highlights(surf)

        for u in self.units:
            if u.is_alive():
                u.draw(surf, self.ui.small)

        label = (
            f"Turn: {team_name(self.turn_team)}"
            if self.winner is None
            else f"{team_name(self.winner)} wins"
        )

        panel_lines = [label] + list(self.log_lines)
        self.ui.draw_panel(surf, panel_lines)