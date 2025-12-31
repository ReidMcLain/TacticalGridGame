import pygame
from collections import deque
from .grid import Grid
from .units import make_starting_units, team_name
from .constants import TILE_SIZE, BLACK, HIGHLIGHT_MOVE, HIGHLIGHT_ATTACK, HIGHLIGHT_SELECT

AI_TEAM = 1

AI_DELAY_UNIT_START_MS = 300
AI_DELAY_AFTER_MOVE_MS = 300
AI_DELAY_BETWEEN_UNITS_MS = 300


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
        self.ai_queue = deque()
        self.ai_timer_ms = 0
        self.ai_phase = "idle"
        self.ai_current = None

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

    def enemy_occupied_cells(self, team):
        return {(u.x, u.y) for u in self.units if u.is_alive() and u.team != team}

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
        moving_unit = self.unit_at(*start)
        moving_team = moving_unit.team if moving_unit else self.turn_team
        blocked = self.enemy_occupied_cells(moving_team) - {start}

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
            blocked = self.enemy_occupied_cells(unit.team) - {unit.pos()}
            self.reachable = self.grid.reachable_cells(unit.pos(), unit.move_points, blocked)

            occupied = self.occupied_cells() - {unit.pos()}
            self.reachable = self.reachable - occupied

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

        if not self.in_ai_turn:
            self.check_auto_end_turn()

    def start_ai_turn(self):
        if self.winner is not None:
            return

        self.in_ai_turn = True
        self.ai_queue = deque([u for u in self.units_alive(AI_TEAM) if not u.acted])
        self.ai_timer_ms = AI_DELAY_UNIT_START_MS
        self.ai_phase = "next_unit"
        self.ai_current = None

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
            self.start_ai_turn()

    def attack(self, attacker, defender):
        if not attacker or not defender:
            return
        if attacker.acted:
            return

        before = defender.hp
        base = int(attacker.hp * 0.40)
        dmg = max(1, base - self.grid.def_bonus(defender.x, defender.y))

        defender.hp -= dmg
        if defender.hp < 0:
            defender.hp = 0

        self._log(
            f"{team_name(attacker.team)} {attacker.kind} attacked "
            f"{team_name(defender.team)} {defender.kind} for {dmg} ({before}->{defender.hp})"
        )

        attacker.start_attack_anim()

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

        if cell == self.selected.pos():
            self.clear_selection()
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

    def update_ai(self, dt_ms):
        if self.winner is not None:
            self.in_ai_turn = False
            self.ai_phase = "idle"
            self.ai_current = None
            self.ai_queue.clear()
            return

        if not self.in_ai_turn:
            self.start_ai_turn()
            return

        if self.animating_unit is not None:
            return

        if self.ai_timer_ms > 0:
            self.ai_timer_ms -= int(dt_ms)
            if self.ai_timer_ms > 0:
                return
            self.ai_timer_ms = 0

        if self.ai_phase == "next_unit":
            while self.ai_queue:
                u = self.ai_queue.popleft()
                if u.is_alive() and not u.acted:
                    self.ai_current = u
                    self.selected = u
                    self.ensure_flags(u)
                    self.compute_reachable_and_attackables(u)
                    self.ai_phase = "act"
                    self.ai_timer_ms = AI_DELAY_UNIT_START_MS
                    return

            self.in_ai_turn = False
            self.ai_phase = "idle"
            self.ai_current = None
            self.end_turn()
            return

        if self.ai_phase == "post_move":
            unit = self.ai_current
            if unit is None or (not unit.is_alive()) or unit.acted:
                self.ai_current = None
                self.ai_phase = "next_unit"
                self.ai_timer_ms = AI_DELAY_BETWEEN_UNITS_MS
                return

            self.selected = unit
            self.compute_reachable_and_attackables(unit)

            if self.attackables:
                self.attack(unit, self.unit_at(*next(iter(self.attackables))))
                if self.winner is not None:
                    self.in_ai_turn = False
                    self.ai_phase = "idle"
                    return
            else:
                self.finish_unit_turn(unit)

            self.ai_current = None
            self.ai_phase = "next_unit"
            self.ai_timer_ms = AI_DELAY_BETWEEN_UNITS_MS
            return

        if self.ai_phase == "act":
            unit = self.ai_current
            if unit is None or (not unit.is_alive()) or unit.acted:
                self.ai_current = None
                self.ai_phase = "next_unit"
                self.ai_timer_ms = AI_DELAY_BETWEEN_UNITS_MS
                return

            self.selected = unit
            self.compute_reachable_and_attackables(unit)

            if self.attackables:
                self.attack(unit, self.unit_at(*next(iter(self.attackables))))
                if self.winner is not None:
                    self.in_ai_turn = False
                    self.ai_phase = "idle"
                    return
                self.ai_current = None
                self.ai_phase = "next_unit"
                self.ai_timer_ms = AI_DELAY_BETWEEN_UNITS_MS
                return

            enemies = self.units_alive(0)
            if not enemies:
                self.finish_unit_turn(unit)
                if self.winner is not None:
                    self.in_ai_turn = False
                    self.ai_phase = "idle"
                    return
                self.ai_current = None
                self.ai_phase = "next_unit"
                self.ai_timer_ms = AI_DELAY_BETWEEN_UNITS_MS
                return

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
                    self.ai_phase = "moving"
                    return

            self.finish_unit_turn(unit)
            if self.winner is not None:
                self.in_ai_turn = False
                self.ai_phase = "idle"
                return

            self.ai_current = None
            self.ai_phase = "next_unit"
            self.ai_timer_ms = AI_DELAY_BETWEEN_UNITS_MS
            return

    def update(self, dt_ms):
        for u in self.units:
            if u.is_alive():
                u.update_attack(dt_ms)

        if self.animating_unit:
            self.animating_unit.update(dt_ms)
            if not self.animating_unit.moving:
                moved_unit = self.animating_unit
                self.animating_unit = None

                if moved_unit.team == AI_TEAM:
                    self.ai_current = moved_unit
                    self.selected = moved_unit
                    self.compute_reachable_and_attackables(moved_unit)
                    self.ai_phase = "post_move"
                    self.ai_timer_ms = AI_DELAY_AFTER_MOVE_MS
                    return

                self.selected = moved_unit
                self.compute_reachable_and_attackables(moved_unit)

                if not self.attackables:
                    self.finish_unit_turn(moved_unit)
                return

        if self.turn_team == AI_TEAM and self.winner is None:
            self.update_ai(dt_ms)

    def draw_highlights(self, surf):
        if self.turn_team == AI_TEAM:
            return

        if self.selected and self.selected.team != self.turn_team:
            return

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
                u.draw(surf, self.ui.small, self.turn_team)

        label = (
            f"Turn: {team_name(self.turn_team)}"
            if self.winner is None
            else f"{team_name(self.winner)} wins"
        )

        panel_lines = [label] + list(self.log_lines)
        self.ui.draw_panel(surf, panel_lines)