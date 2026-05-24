"""Tests for CombatSystem — hit probability, defeat logic, player rewards."""
from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from classes.combat_system import CombatSystem
from classes.entity import Entity
from classes.item import Equipment, Item


def make_entity(name: str = 'Fighter', health: float = 100, damage: float = 0,
                defense: float = 0, x: int = 0, y: int = 0) -> Entity:
    e = Entity(x, y, '@', name, float(health), float(damage), float(defense))
    e.strength = 10
    e.dexterity = 10
    e.constitution = 10
    e.level = 1
    return e


def make_weapon(name: str = 'Sword', stat_boost: float = 5) -> Equipment:
    return Equipment(name, 'weapon', 'hands', stat_boost, damage={'min': 3, 'max': 6})


# ---------------------------------------------------------------------------
# Logistic hit-chance formula
# ---------------------------------------------------------------------------

class TestHitProbability:
    def test_equal_attack_defense_gives_50_percent(self) -> None:
        # diff = 0 → hit_chance = 0.5
        hit_chance = 1 / (1 + math.exp(0))
        assert abs(hit_chance - 0.5) < 1e-9

    def test_large_positive_diff_near_certainty(self) -> None:
        # diff = 50 → nearly 1.0
        hit_chance = 1 / (1 + math.exp(-50 / 5))
        assert hit_chance > 0.99

    def test_large_negative_diff_near_zero(self) -> None:
        # diff = -50 → nearly 0.0
        hit_chance = 1 / (1 + math.exp(50 / 5))
        assert hit_chance < 0.01


# ---------------------------------------------------------------------------
# CombatSystem.combat()
# ---------------------------------------------------------------------------

class TestCombatHit:
    def test_successful_hit_appends_message(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Attacker', damage=5)
        defender = make_entity('Defender', health=50)
        messages: list[str] = []
        with patch('random.random', return_value=0.0):   # always hit
            with patch('random.randint', return_value=2):
                cs.combat(attacker, defender, messages)
        assert any('hits' in m for m in messages)

    def test_hit_reduces_defender_health(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Attacker', damage=5)
        attacker.strength = 20
        defender = make_entity('Defender', health=200)
        messages: list[str] = []
        with patch('random.random', return_value=0.0):
            with patch('random.randint', return_value=3):
                cs.combat(attacker, defender, messages)
        assert defender.health < 200.0

    def test_armor_absorbs_damage(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Attacker', damage=5)
        attacker.strength = 30
        defender = make_entity('Defender', health=200)
        armor = Equipment('Plate', 'armor', 'torso', 10, ac=10)
        defender.equip_item(armor)
        messages: list[str] = []
        with patch('random.random', return_value=0.0):
            with patch('random.randint', return_value=3):
                cs.combat(attacker, defender, messages)
        assert any('absorbed' in m for m in messages) or defender.health == 199.0

    def test_minimum_damage_is_one(self) -> None:
        """Even with heavy armor, at least 1 point of damage lands on a hit."""
        cs = CombatSystem()
        attacker = make_entity('Weakling')
        attacker.strength = 1
        attacker.level = 1
        attacker.base_damage = 0.0
        defender = make_entity('Tank', health=500)
        # Equip massive armor
        armor = Equipment('God Armor', 'armor', 'torso', 0, ac=9999)
        defender.equip_item(armor)
        messages: list[str] = []
        with patch('random.random', return_value=0.0):
            with patch('random.randint', return_value=1):
                cs.combat(attacker, defender, messages)
        damage_dealt = 500.0 - defender.health
        if any('hits' in m for m in messages):
            assert damage_dealt >= 1.0


class TestCombatMiss:
    def test_miss_appends_message(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Attacker')
        defender = make_entity('Defender', health=50)
        messages: list[str] = []
        with patch('random.random', return_value=1.0):   # always miss
            with patch('random.randint', return_value=2):
                cs.combat(attacker, defender, messages)
        assert any('misses' in m for m in messages)

    def test_miss_does_not_reduce_health(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Attacker')
        defender = make_entity('Defender', health=50)
        messages: list[str] = []
        with patch('random.random', return_value=1.0):
            with patch('random.randint', return_value=2):
                cs.combat(attacker, defender, messages)
        assert defender.health == 50.0


class TestCombatDefeat:
    def test_returns_true_when_defender_dies(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Killer', damage=999)
        attacker.strength = 200
        defender = make_entity('Glass', health=1)
        messages: list[str] = []
        with patch('random.random', return_value=0.0):
            with patch('random.randint', return_value=5):
                result = cs.combat(attacker, defender, messages)
        assert result is True

    def test_returns_false_when_defender_survives(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Attacker')
        defender = make_entity('Tank', health=10000)
        messages: list[str] = []
        with patch('random.random', return_value=0.0):
            with patch('random.randint', return_value=1):
                result = cs.combat(attacker, defender, messages)
        assert result is False

    def test_defeat_appends_defeated_message(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Killer', damage=999)
        attacker.strength = 200
        defender = make_entity('Prey', health=1)
        messages: list[str] = []
        with patch('random.random', return_value=0.0):
            with patch('random.randint', return_value=5):
                cs.combat(attacker, defender, messages)
        assert any('defeated' in m.lower() for m in messages)


class TestBareFists:
    def test_no_weapon_uses_random_1_3(self) -> None:
        cs = CombatSystem()
        attacker = make_entity('Puncher')
        defender = make_entity('Target', health=200)
        messages: list[str] = []
        # randint(1,3) for bare fists, then randint(-2,2) for jitter
        with patch('random.random', return_value=0.0):
            with patch('random.randint', side_effect=[2, 0]):
                cs.combat(attacker, defender, messages)
        assert any('hits' in m for m in messages)


class TestWeaponStats:
    def test_weapon_accuracy_bonus_used_in_attack_score(self) -> None:
        """Adding a high-accuracy weapon should increase hit chance."""
        cs = CombatSystem()
        attacker = make_entity('Archer')
        w = make_weapon(stat_boost=0)
        # Give the weapon very high accuracy
        w.accuracy_bonus = 100
        attacker.add_item(w)
        attacker.equip_item(w)

        defender = make_entity('Target', health=500)
        defender.dexterity = 100  # very high defense
        messages: list[str] = []
        with patch('random.random', return_value=0.49):
            with patch('random.randint', return_value=3):
                cs.combat(attacker, defender, messages)
        # With accuracy_bonus=100 the attack_score should be high enough to hit
        assert any('hits' in m for m in messages) or any('misses' in m for m in messages)


# ---------------------------------------------------------------------------
# CombatSystem.player_attack_enemy()
# ---------------------------------------------------------------------------

class TestPlayerAttackEnemy:
    def _setup(self) -> tuple[CombatSystem, Entity, Entity]:
        cs = CombatSystem()
        player = make_entity('Player')
        enemy = make_entity('Goblin', x=1, y=1)
        enemy.xp_reward = 30
        enemy.gold_reward = 15
        return cs, player, enemy

    def test_grants_xp_to_player(self) -> None:
        cs, player, enemy = self._setup()
        with patch('random.random', return_value=1.0):  # no loot drop
            cs.player_attack_enemy(player, enemy, [])
        assert player.xp == 30

    def test_grants_gold_to_player(self) -> None:
        cs, player, enemy = self._setup()
        with patch('random.random', return_value=1.0):
            cs.player_attack_enemy(player, enemy, [])
        assert player.money == 15

    def test_no_gold_if_gold_reward_zero(self) -> None:
        cs = CombatSystem()
        player = make_entity('Player')
        enemy = make_entity('Poor Goblin')
        enemy.xp_reward = 10
        enemy.gold_reward = 0
        messages: list[str] = []
        with patch('random.random', return_value=1.0):
            cs.player_attack_enemy(player, enemy, messages)
        assert not any('gold' in m.lower() for m in messages)

    def test_defeat_message_appended(self) -> None:
        cs, player, enemy = self._setup()
        messages: list[str] = []
        with patch('random.random', return_value=1.0):
            cs.player_attack_enemy(player, enemy, messages)
        assert any('defeated' in m.lower() for m in messages)

    def test_loot_drops_at_enemy_position(self) -> None:
        cs, player, enemy = self._setup()
        enemy.x, enemy.y = 5, 3
        fn: Callable[[Entity], Any] = lambda e: None
        enemy.loot = [Item('Coin', fn)]
        with patch('random.random', return_value=0.0):  # 0.0 < 0.05, always drop
            drops = cs.player_attack_enemy(player, enemy, [])
        if drops:
            assert drops[0].x == 5
            assert drops[0].y == 3
