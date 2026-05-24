from __future__ import annotations

import random
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from classes.entity import Entity
    from classes.combat_system import CombatSystem

# Noise levels emitted by various actions
FOOTSTEP_NOISE: float = 2.0
DOOR_NOISE: float = 5.0
COMBAT_NOISE: float = 10.0
_SHOUT_NOISE: float = 8.0
_ALERT_NOISE_THRESHOLD: float = 8.0

SLEEP_SPAWN_CHANCE: float = 0.40


class _GameLike(Protocol):
    player: Entity
    messages: list[str]
    map: list[list[str]]
    combat_system: CombatSystem
    enemies: list[Entity]
    noise_events: list[tuple[int, int, float]]
    width: int
    height: int

    def distance(self, entity1: Entity, entity2: Entity) -> float: ...
    def has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool: ...
    def get_flow_next_step(self, enemy: Entity) -> tuple[int, int] | None: ...
    def handle_player_death(self) -> None: ...
    def invalidate_flow_field(self) -> None: ...
    def emit_noise(self, x: int, y: int, level: float) -> None: ...


class AISystem:
    def run_action(self, enemy: Entity, game: _GameLike) -> None:
        state = enemy.ai_state.state

        if state == "asleep":
            self._check_wake(enemy, game)
            return

        if state == "idle":
            self._check_wake(enemy, game)
            if enemy.ai_state.state == "idle":
                if self._can_see_player(enemy, game):
                    self._become_alert(enemy, game, reason="spots")
                else:
                    self._wander(enemy, game)
                    return
            state = enemy.ai_state.state

        if state == "alert":
            if (game.distance(enemy, game.player) <= 1 and
                    game.has_line_of_sight(enemy.x, enemy.y, game.player.x, game.player.y)):
                defeated = game.combat_system.combat(enemy, game.player, game.messages)
                game.emit_noise(enemy.x, enemy.y, COMBAT_NOISE)
                if defeated:
                    game.handle_player_death()
            else:
                next_pos = game.get_flow_next_step(enemy)
                if next_pos:
                    if game.map[next_pos[1]][next_pos[0]] == '+':
                        game.map[next_pos[1]][next_pos[0]] = '/'
                        game.invalidate_flow_field()
                    else:
                        enemy.x, enemy.y = next_pos

    def _can_see_player(self, enemy: Entity, game: _GameLike) -> bool:
        dist = game.distance(enemy, game.player)
        return (dist <= enemy.perception and
                game.has_line_of_sight(enemy.x, enemy.y, game.player.x, game.player.y))

    def _become_alert(self, enemy: Entity, game: _GameLike, reason: str = "spots") -> None:
        if enemy.ai_state.state == "alert":
            return
        enemy.ai_state.state = "alert"
        game.emit_noise(enemy.x, enemy.y, _SHOUT_NOISE)
        if reason == "spots":
            game.messages.append(f"The {enemy.name} spots you!")
        elif reason == "wakes":
            game.messages.append(f"The {enemy.name} wakes with a start!")
        else:
            game.messages.append(f"The {enemy.name} is alerted!")

    def _check_wake(self, enemy: Entity, game: _GameLike) -> None:
        is_asleep = enemy.ai_state.state == "asleep"
        perception_mult = 0.5 if is_asleep else 1.0
        for nx, ny, level in game.noise_events:
            dist = max(abs(enemy.x - nx), abs(enemy.y - ny))
            hearing_range = level * (enemy.perception / 10.0) * perception_mult
            if dist <= hearing_range:
                if is_asleep:
                    if level >= _ALERT_NOISE_THRESHOLD:
                        self._become_alert(enemy, game, reason="wakes")
                    else:
                        enemy.ai_state.state = "idle"
                    return
                elif level >= _ALERT_NOISE_THRESHOLD:
                    self._become_alert(enemy, game, reason="hears")
                    return

    def _wander(self, enemy: Entity, game: _GameLike) -> None:
        dirs = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
            (0, 0),
        ]
        if enemy.ai_state.wander_turns_left > 0:
            dx, dy = enemy.ai_state.wander_dx, enemy.ai_state.wander_dy
            enemy.ai_state.wander_turns_left -= 1
        else:
            dx, dy = random.choice(dirs)
            enemy.ai_state.wander_dx = dx
            enemy.ai_state.wander_dy = dy
            enemy.ai_state.wander_turns_left = random.randint(3, 6)

        if dx == 0 and dy == 0:
            return

        nx, ny = enemy.x + dx, enemy.y + dy
        occupied = {(e.x, e.y) for e in game.enemies if e is not enemy}
        if (0 <= nx < game.width and 0 <= ny < game.height and
                game.map[ny][nx] in ('.', '/') and
                (nx, ny) not in occupied and
                (nx, ny) != (game.player.x, game.player.y)):
            enemy.x, enemy.y = nx, ny
        else:
            enemy.ai_state.wander_turns_left = 0
