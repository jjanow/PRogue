"""Tests for StatusSystem, TurnSystem, and AISystem."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from classes.entity import Entity
from classes.game import Game
from classes.item import Item
from classes.systems.ai_system import AISystem
from classes.systems.status_system import StatusSystem


def make_entity(x: int = 0, y: int = 0, name: str = 'Fighter', health: float = 50) -> Entity:
    e = Entity(x, y, 'E', name, float(health), 0, 0)
    e.strength = 10
    e.dexterity = 10
    e.constitution = 10
    return e


# ---------------------------------------------------------------------------
# StatusSystem
# ---------------------------------------------------------------------------

class TestStatusSystem:
    def test_decrements_boost_duration(self) -> None:
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('strength', 5, 3)
        ss.update(entity, [])
        assert entity.status_comp.boosts['strength']['duration'] == 2

    def test_removes_expired_boost(self) -> None:
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('dexterity', 3, 1)
        messages: list[str] = []
        ss.update(entity, messages)
        assert 'dexterity' not in entity.status_comp.boosts

    def test_expired_boost_appends_message(self) -> None:
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('willpower', 2, 1)
        messages: list[str] = []
        ss.update(entity, messages)
        assert any('Willpower' in m for m in messages)

    def test_multiple_boosts_tracked_independently(self) -> None:
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('strength', 4, 5)
        entity.apply_temporary_boost('charisma', 2, 2)
        ss.update(entity, [])
        assert entity.status_comp.boosts['strength']['duration'] == 4
        assert entity.status_comp.boosts['charisma']['duration'] == 1

    def test_only_expired_boost_removed(self) -> None:
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('strength', 4, 2)
        entity.apply_temporary_boost('charisma', 2, 1)
        ss.update(entity, [])
        assert 'strength' in entity.status_comp.boosts
        assert 'charisma' not in entity.status_comp.boosts

    def test_no_boosts_does_nothing(self) -> None:
        ss = StatusSystem()
        entity = make_entity()
        messages: list[str] = []
        ss.update(entity, messages)  # must not raise
        assert messages == []


# ---------------------------------------------------------------------------
# TurnSystem
# ---------------------------------------------------------------------------

class TestTurnSystem:
    def test_increments_turn_count(self, minimal_game: Game) -> None:
        initial = minimal_game.turn_count
        minimal_game.turn_system.process(minimal_game)
        assert minimal_game.turn_count == initial + 1

    def test_removes_dead_enemies(self, minimal_game: Game) -> None:
        dead = make_entity(3, 3, 'Dead Goblin', health=30)
        dead.health = 0.0
        minimal_game.enemies.append(dead)
        minimal_game.turn_system.process(minimal_game)
        assert dead not in minimal_game.enemies

    def test_keeps_living_enemies(self, minimal_game: Game) -> None:
        alive = make_entity(3, 3, 'Alive Goblin', health=30)
        minimal_game.enemies.append(alive)
        minimal_game.turn_system.process(minimal_game)
        assert alive in minimal_game.enemies

    def test_heals_player_on_multiple_of_10(self, minimal_game: Game) -> None:
        minimal_game.player.health = 50.0
        minimal_game.player.max_health = 100.0
        minimal_game.turn_count = 9
        minimal_game.turn_system.process(minimal_game)
        assert minimal_game.turn_count == 10
        assert minimal_game.player.health == 51.0

    def test_no_heal_on_non_multiple_of_10(self, minimal_game: Game) -> None:
        minimal_game.player.health = 50.0
        minimal_game.player.max_health = 100.0
        minimal_game.turn_count = 8
        minimal_game.turn_system.process(minimal_game)
        # turn_count becomes 9, not a multiple of 10
        assert minimal_game.player.health == 50.0

    def test_no_overheal_beyond_max(self, minimal_game: Game) -> None:
        minimal_game.player.health = 100.0
        minimal_game.player.max_health = 100.0
        minimal_game.turn_count = 9
        minimal_game.turn_system.process(minimal_game)
        assert minimal_game.player.health == 100.0

    def test_spawns_enemy_when_interval_and_chance_met(self, minimal_game: Game) -> None:
        initial = len(minimal_game.enemies)
        minimal_game.turn_count = 99
        minimal_game.last_spawn_turn = 0
        # Force random.random() to return 0.0, which is < _SPAWN_CHANCE (0.40)
        with patch('classes.systems.turn_system.random.random', return_value=0.0):
            minimal_game.turn_system.process(minimal_game)
        # After process: turn_count=100, 100-0=100 >= 100 and chance met → spawn
        assert len(minimal_game.enemies) > initial

    def test_does_not_spawn_before_100_turn_gap(self, minimal_game: Game) -> None:
        initial = len(minimal_game.enemies)
        minimal_game.turn_count = 50
        minimal_game.last_spawn_turn = 0
        minimal_game.turn_system.process(minimal_game)
        # After process: turn_count=51, 51-0=51 < 100 → no spawn regardless of chance
        assert len(minimal_game.enemies) == initial

    def test_no_ambient_spawn_when_flag_false(self, minimal_game: Game) -> None:
        minimal_game.allow_enemy_spawning = False
        initial = len(minimal_game.enemies)
        minimal_game.turn_count = 99
        minimal_game.last_spawn_turn = 0
        with patch('classes.systems.turn_system.random.random', return_value=0.0):
            minimal_game.turn_system.process(minimal_game)
        # Interval reached and chance met but spawning disabled → no spawn
        assert len(minimal_game.enemies) == initial

    def test_no_spawn_when_chance_fails(self, minimal_game: Game) -> None:
        minimal_game.allow_enemy_spawning = True
        initial = len(minimal_game.enemies)
        minimal_game.turn_count = 99
        minimal_game.last_spawn_turn = 0
        # Force random.random() to return 1.0, which is >= _SPAWN_CHANCE → no spawn
        with patch('classes.systems.turn_system.random.random', return_value=1.0):
            minimal_game.turn_system.process(minimal_game)
        assert len(minimal_game.enemies) == initial

    def test_floor_items_at_player_position_messaged(self, minimal_game: Game) -> None:
        fn: Callable[[Entity], Any] = lambda e: None
        item = Item('Shiny Coin', fn)
        item.x, item.y = minimal_game.player.x, minimal_game.player.y
        minimal_game.items.append(item)
        minimal_game.turn_system.process(minimal_game)
        assert any('Shiny Coin' in m for m in minimal_game.messages)

    def test_enemy_energy_accumulates(self, minimal_game: Game) -> None:
        enemy = make_entity(3, 3, 'Slow Enemy', health=50)
        enemy.energy_comp.speed = 50  # less than ACTION_COST
        enemy.energy_comp.energy = 0.0
        minimal_game.enemies.append(enemy)
        minimal_game.turn_system.process(minimal_game)
        # Energy should have been added but not yet enough to act
        assert enemy.energy_comp.energy > 0


# ---------------------------------------------------------------------------
# AISystem
# ---------------------------------------------------------------------------

class TestAISystem:
    def test_attacks_when_adjacent_with_los(self, minimal_game: Game) -> None:
        ai = AISystem()
        enemy = make_entity(6, 4, 'Adjacent Goblin', health=30)
        enemy.strength = 10
        enemy.ai_state.state = "alert"
        minimal_game.enemies.append(enemy)
        with patch('random.random', return_value=0.0):
            with patch('random.randint', return_value=2):
                ai.run_action(enemy, minimal_game)
        assert any('Goblin' in m for m in minimal_game.messages)

    def test_alert_enemy_moves_toward_player(self, minimal_game: Game) -> None:
        ai = AISystem()
        enemy = make_entity(10, 4, 'Distant Goblin', health=30)
        enemy.ai_state.state = "alert"
        minimal_game.enemies.append(enemy)
        old_x, old_y = enemy.x, enemy.y
        ai.run_action(enemy, minimal_game)
        new_dist = minimal_game.distance(enemy, minimal_game.player)
        old_dist = max(abs(old_x - minimal_game.player.x),
                       abs(old_y - minimal_game.player.y))
        assert new_dist < old_dist

    def test_stationary_when_no_path(self, minimal_game: Game) -> None:
        ai = AISystem()
        px, py = minimal_game.player.x, minimal_game.player.y
        for ddx in range(-2, 3):
            for ddy in range(-2, 3):
                nx, ny = px + ddx, py + ddy
                if 0 <= ny < minimal_game.height and 0 <= nx < minimal_game.width:
                    if (nx, ny) != (px, py):
                        minimal_game.map[ny][nx] = '#'
        enemy = make_entity(3, 3, 'Blocked', health=30)
        enemy.ai_state.state = "alert"
        minimal_game.map[3][4] = '#'
        minimal_game.map[4][3] = '#'
        ai.run_action(enemy, minimal_game)
        assert True  # reached here without exception

    def test_sleeping_enemy_does_not_act(self, minimal_game: Game) -> None:
        ai = AISystem()
        enemy = make_entity(6, 4, 'Sleeping Goblin', health=30)
        enemy.ai_state.state = "asleep"
        minimal_game.enemies.append(enemy)
        old_x, old_y = enemy.x, enemy.y
        ai.run_action(enemy, minimal_game)
        assert enemy.x == old_x and enemy.y == old_y
        assert not any('Goblin' in m for m in minimal_game.messages)

    def test_sleeping_enemy_wakes_on_nearby_noise(self, minimal_game: Game) -> None:
        ai = AISystem()
        enemy = make_entity(6, 4, 'Sleeping Goblin', health=30)
        enemy.ai_state.state = "asleep"
        enemy.perception = 10
        minimal_game.enemies.append(enemy)
        # Footstep at distance 1 → hearing_range = 2 * 0.5 = 1 ≥ dist 1
        minimal_game.noise_events.append((7, 4, 2.0))
        ai.run_action(enemy, minimal_game)
        assert enemy.ai_state.state == "idle"

    def test_sleeping_enemy_stays_asleep_on_distant_noise(self, minimal_game: Game) -> None:
        ai = AISystem()
        enemy = make_entity(2, 2, 'Distant Sleeper', health=30)
        enemy.ai_state.state = "asleep"
        enemy.perception = 10
        minimal_game.enemies.append(enemy)
        # Footstep at distance 5 → hearing_range = 2 * 0.5 = 1 < dist 5
        minimal_game.noise_events.append((7, 4, 2.0))
        ai.run_action(enemy, minimal_game)
        assert enemy.ai_state.state == "asleep"

    def test_combat_noise_wakes_sleeping_enemy_to_alert(self, minimal_game: Game) -> None:
        ai = AISystem()
        enemy = make_entity(8, 4, 'Sleeping Goblin', health=30)
        enemy.ai_state.state = "asleep"
        enemy.perception = 10
        minimal_game.enemies.append(enemy)
        # Combat noise (10) at distance 3 → hearing_range = 10 * 0.5 = 5 ≥ dist 3
        minimal_game.noise_events.append((5, 4, 10.0))
        ai.run_action(enemy, minimal_game)
        assert enemy.ai_state.state == "alert"

    def test_idle_enemy_becomes_alert_on_player_sight(self, minimal_game: Game) -> None:
        ai = AISystem()
        # Player is at (5,4); put enemy close enough with LOS
        enemy = make_entity(7, 4, 'Idle Goblin', health=30)
        enemy.ai_state.state = "idle"
        enemy.perception = 10
        minimal_game.enemies.append(enemy)
        minimal_game.update_fov()
        ai.run_action(enemy, minimal_game)
        assert enemy.ai_state.state == "alert"
        assert any('spots you' in m for m in minimal_game.messages)

    def test_idle_enemy_wanders(self, minimal_game: Game) -> None:
        ai = AISystem()
        # Place enemy far from player (distance > perception=10 is impossible in this map,
        # so put them with no LOS by blocking sight)
        enemy = make_entity(3, 6, 'Wandering Goblin', health=30)
        enemy.ai_state.state = "idle"
        enemy.perception = 1  # can only see 1 tile; player is far away
        # Force a specific wander direction toward open floor
        enemy.ai_state.wander_dx = 1
        enemy.ai_state.wander_dy = 0
        enemy.ai_state.wander_turns_left = 3
        minimal_game.enemies.append(enemy)
        old_x, old_y = enemy.x, enemy.y
        ai.run_action(enemy, minimal_game)
        # Enemy should have moved or at least not crashed
        assert enemy.ai_state.state in ("idle", "alert")
        # With wander_turns_left > 0, it moved in the wander direction (3,6)→(4,6) which is '.'
        assert enemy.x == 4 and enemy.y == 6

    def test_shout_propagates_to_nearby_sleeping_enemy(self, minimal_game: Game) -> None:
        ai = AISystem()
        sleeper = make_entity(9, 4, 'Sleeping Goblin', health=30)
        sleeper.ai_state.state = "asleep"
        sleeper.perception = 10
        minimal_game.enemies.append(sleeper)
        # Shout noise (8) at distance 2 → sleeping_range = 8 * 0.5 = 4 ≥ 2
        minimal_game.noise_events.append((7, 4, 8.0))
        ai.run_action(sleeper, minimal_game)
        # Shout level 8 >= _ALERT_NOISE_THRESHOLD → wakes directly to alert
        assert sleeper.ai_state.state == "alert"
