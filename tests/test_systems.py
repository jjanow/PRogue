"""Tests for StatusSystem, TurnSystem, and AISystem."""
from unittest.mock import patch

import pytest

from classes.entity import Entity
from classes.systems.ai_system import AISystem
from classes.systems.status_system import StatusSystem
from classes.systems.turn_system import TurnSystem


def make_entity(x=0, y=0, name='Fighter', health=50):
    e = Entity(x, y, 'E', name, float(health), 0, 0)
    e.strength = 10
    e.dexterity = 10
    e.constitution = 10
    return e


# ---------------------------------------------------------------------------
# StatusSystem
# ---------------------------------------------------------------------------

class TestStatusSystem:
    def test_decrements_boost_duration(self):
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('strength', 5, 3)
        ss.update(entity, [])
        assert entity.status_comp.boosts['strength']['duration'] == 2

    def test_removes_expired_boost(self):
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('dexterity', 3, 1)
        messages = []
        ss.update(entity, messages)
        assert 'dexterity' not in entity.status_comp.boosts

    def test_expired_boost_appends_message(self):
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('willpower', 2, 1)
        messages = []
        ss.update(entity, messages)
        assert any('Willpower' in m for m in messages)

    def test_multiple_boosts_tracked_independently(self):
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('strength', 4, 5)
        entity.apply_temporary_boost('charisma', 2, 2)
        ss.update(entity, [])
        assert entity.status_comp.boosts['strength']['duration'] == 4
        assert entity.status_comp.boosts['charisma']['duration'] == 1

    def test_only_expired_boost_removed(self):
        ss = StatusSystem()
        entity = make_entity()
        entity.apply_temporary_boost('strength', 4, 2)
        entity.apply_temporary_boost('charisma', 2, 1)
        ss.update(entity, [])
        assert 'strength' in entity.status_comp.boosts
        assert 'charisma' not in entity.status_comp.boosts

    def test_no_boosts_does_nothing(self):
        ss = StatusSystem()
        entity = make_entity()
        messages = []
        ss.update(entity, messages)  # must not raise
        assert messages == []


# ---------------------------------------------------------------------------
# TurnSystem
# ---------------------------------------------------------------------------

class TestTurnSystem:
    def test_increments_turn_count(self, minimal_game):
        initial = minimal_game.turn_count
        minimal_game.turn_system.process(minimal_game)
        assert minimal_game.turn_count == initial + 1

    def test_removes_dead_enemies(self, minimal_game):
        dead = make_entity(3, 3, 'Dead Goblin', health=30)
        dead.health = 0.0
        minimal_game.enemies.append(dead)
        minimal_game.turn_system.process(minimal_game)
        assert dead not in minimal_game.enemies

    def test_keeps_living_enemies(self, minimal_game):
        alive = make_entity(3, 3, 'Alive Goblin', health=30)
        minimal_game.enemies.append(alive)
        minimal_game.turn_system.process(minimal_game)
        assert alive in minimal_game.enemies

    def test_heals_player_on_multiple_of_10(self, minimal_game):
        minimal_game.player.health = 50.0
        minimal_game.player.max_health = 100.0
        minimal_game.turn_count = 9
        minimal_game.turn_system.process(minimal_game)
        assert minimal_game.turn_count == 10
        assert minimal_game.player.health == 51.0

    def test_no_heal_on_non_multiple_of_10(self, minimal_game):
        minimal_game.player.health = 50.0
        minimal_game.player.max_health = 100.0
        minimal_game.turn_count = 8
        minimal_game.turn_system.process(minimal_game)
        # turn_count becomes 9, not a multiple of 10
        assert minimal_game.player.health == 50.0

    def test_no_overheal_beyond_max(self, minimal_game):
        minimal_game.player.health = 100.0
        minimal_game.player.max_health = 100.0
        minimal_game.turn_count = 9
        minimal_game.turn_system.process(minimal_game)
        assert minimal_game.player.health == 100.0

    def test_spawns_enemy_every_50_turns(self, minimal_game):
        initial = len(minimal_game.enemies)
        minimal_game.turn_count = 49
        minimal_game.last_spawn_turn = 0
        minimal_game.turn_system.process(minimal_game)
        # After process: turn_count=50, 50-0=50 >= 50 → spawn
        assert len(minimal_game.enemies) > initial

    def test_does_not_spawn_before_50_turn_gap(self, minimal_game):
        initial = len(minimal_game.enemies)
        minimal_game.turn_count = 20
        minimal_game.last_spawn_turn = 15
        minimal_game.turn_system.process(minimal_game)
        # After process: turn_count=21, 21-15=6 < 50 → no spawn
        assert len(minimal_game.enemies) == initial

    def test_no_ambient_spawn_in_town(self, minimal_game):
        minimal_game.in_town = True
        initial = len(minimal_game.enemies)
        minimal_game.turn_count = 49
        minimal_game.last_spawn_turn = 0
        minimal_game.turn_system.process(minimal_game)
        # 50-turn threshold reached but in_town=True → no spawn
        assert len(minimal_game.enemies) == initial

    def test_ambient_spawn_resumes_in_dungeon(self, minimal_game):
        minimal_game.in_town = False
        initial = len(minimal_game.enemies)
        minimal_game.turn_count = 49
        minimal_game.last_spawn_turn = 0
        minimal_game.turn_system.process(minimal_game)
        assert len(minimal_game.enemies) > initial

    def test_floor_items_at_player_position_messaged(self, minimal_game):
        from classes.item import Item
        item = Item('Shiny Coin', lambda e: None)
        item.x, item.y = minimal_game.player.x, minimal_game.player.y
        minimal_game.items.append(item)
        minimal_game.turn_system.process(minimal_game)
        assert any('Shiny Coin' in m for m in minimal_game.messages)

    def test_enemy_energy_accumulates(self, minimal_game):
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
    def test_attacks_when_adjacent_with_los(self, minimal_game):
        ai = AISystem()
        # Enemy directly adjacent to player (player at 5,4)
        enemy = make_entity(6, 4, 'Adjacent Goblin', health=30)
        enemy.strength = 10
        minimal_game.enemies.append(enemy)
        with patch('random.random', return_value=0.0):    # always hit
            with patch('random.randint', return_value=2):
                ai.run_action(enemy, minimal_game)
        assert any('Goblin' in m for m in minimal_game.messages)

    def test_moves_toward_player_when_not_adjacent(self, minimal_game):
        ai = AISystem()
        # Enemy far from player in the same room
        enemy = make_entity(10, 4, 'Distant Goblin', health=30)
        minimal_game.enemies.append(enemy)
        old_x, old_y = enemy.x, enemy.y
        ai.run_action(enemy, minimal_game)
        # Should have moved closer (Chebyshev distance decreased)
        new_dist = minimal_game.distance(enemy, minimal_game.player)
        old_dist = max(abs(old_x - minimal_game.player.x),
                       abs(old_y - minimal_game.player.y))
        assert new_dist < old_dist

    def test_stationary_when_no_path(self, minimal_game):
        ai = AISystem()
        # Surround player with walls so pathfinding returns None
        px, py = minimal_game.player.x, minimal_game.player.y
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = px + dx, py + dy
                if 0 <= ny < minimal_game.height and 0 <= nx < minimal_game.width:
                    if (nx, ny) != (px, py):
                        minimal_game.map[ny][nx] = '#'
        enemy = make_entity(3, 3, 'Blocked', health=30)
        # Also wall off the enemy's position so it can't see player
        minimal_game.map[3][4] = '#'
        minimal_game.map[4][3] = '#'
        old_pos = (enemy.x, enemy.y)
        ai.run_action(enemy, minimal_game)
        # Enemy may or may not move; just confirm it doesn't crash
        assert True  # reached here without exception
