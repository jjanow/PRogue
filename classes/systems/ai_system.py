from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from classes.entity import Entity
    from classes.combat_system import CombatSystem


class _GameLike(Protocol):
    player: Entity
    messages: list[str]
    map: list[list[str]]
    combat_system: CombatSystem

    def distance(self, entity1: Entity, entity2: Entity) -> float: ...
    def has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool: ...
    def get_flow_next_step(self, enemy: Entity) -> tuple[int, int] | None: ...
    def handle_player_death(self) -> None: ...
    def invalidate_flow_field(self) -> None: ...


class AISystem:
    def run_action(self, enemy: Entity, game: _GameLike) -> None:
        if (game.distance(enemy, game.player) <= 1 and
                game.has_line_of_sight(enemy.x, enemy.y, game.player.x, game.player.y)):
            defeated = game.combat_system.combat(enemy, game.player, game.messages)
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
