"""Tests for ECS components defined in classes/ecs.py."""
from collections import Counter

from classes.ecs import (
    ACTION_COST,
    AITagComponent,
    CharacterInfoComponent,
    CombatStatsComponent,
    EnergyComponent,
    EquipmentComponent,
    HealthComponent,
    InventoryComponent,
    LootComponent,
    ManaComponent,
    MoneyComponent,
    PlayerTagComponent,
    PositionComponent,
    RenderableComponent,
    StatsComponent,
    StatusEffectsComponent,
)


def test_action_cost_value():
    assert ACTION_COST == 100


class TestPositionComponent:
    def test_stores_coordinates(self):
        p = PositionComponent(3, 7)
        assert p.x == 3
        assert p.y == 7

    def test_mutable(self):
        p = PositionComponent(0, 0)
        p.x = 10
        p.y = 20
        assert p.x == 10
        assert p.y == 20


class TestRenderableComponent:
    def test_stores_char(self):
        r = RenderableComponent('@')
        assert r.char == '@'


class TestHealthComponent:
    def test_stores_health_and_max(self):
        h = HealthComponent(80.0, 100.0)
        assert h.health == 80.0
        assert h.max_health == 100.0


class TestEnergyComponent:
    def test_defaults(self):
        e = EnergyComponent()
        assert e.energy == 0.0
        assert e.speed == 100

    def test_custom_values(self):
        e = EnergyComponent(energy=50.0, speed=120)
        assert e.energy == 50.0
        assert e.speed == 120


class TestStatsComponent:
    def test_all_stats_default_to_10(self):
        s = StatsComponent()
        for stat in ('strength', 'dexterity', 'constitution', 'intelligence',
                     'willpower', 'charisma', 'appearance', 'perception'):
            assert getattr(s, stat) == 10, f"{stat} should default to 10"

    def test_level_defaults(self):
        s = StatsComponent()
        assert s.level == 1
        assert s.xp == 0
        assert s.xp_to_next_level == 100


class TestCombatStatsComponent:
    def test_defaults_to_zero(self):
        c = CombatStatsComponent()
        assert c.base_damage == 0.0
        assert c.base_defense == 0.0

    def test_custom_values(self):
        c = CombatStatsComponent(base_damage=5.0, base_defense=3.0)
        assert c.base_damage == 5.0
        assert c.base_defense == 3.0


class TestInventoryComponent:
    def test_defaults_to_empty_counter(self):
        inv = InventoryComponent()
        assert isinstance(inv.items, Counter)
        assert len(inv.items) == 0


class TestEquipmentComponent:
    def test_defaults_to_empty_dict(self):
        eq = EquipmentComponent()
        assert isinstance(eq.slots, dict)
        assert len(eq.slots) == 0


class TestManaComponent:
    def test_defaults(self):
        m = ManaComponent()
        assert m.mana == 10.0
        assert m.max_mana == 10.0
        assert m.psi == 10.0
        assert m.max_psi == 10.0


class TestCharacterInfoComponent:
    def test_defaults(self):
        c = CharacterInfoComponent()
        assert c.name == ''
        assert c.deity == 'None'
        assert c.birth == 'Unknown'
        assert c.age == 0

    def test_custom_name(self):
        c = CharacterInfoComponent(name='Arthur')
        assert c.name == 'Arthur'


class TestMoneyComponent:
    def test_defaults_to_zero(self):
        m = MoneyComponent()
        assert m.money == 0


class TestPlayerTagComponent:
    def test_constructable(self):
        t = PlayerTagComponent()
        assert t is not None


class TestAITagComponent:
    def test_default_behavior(self):
        a = AITagComponent()
        assert a.behavior == 'basic'

    def test_custom_behavior(self):
        a = AITagComponent(behavior='aggressive')
        assert a.behavior == 'aggressive'


class TestLootComponent:
    def test_defaults(self):
        l = LootComponent()
        assert l.xp_reward == 0
        assert l.gold_reward == 0
        assert l.loot == []


class TestStatusEffectsComponent:
    def test_defaults(self):
        s = StatusEffectsComponent()
        assert s.boosts == {}
        assert s.poisoned is False
        assert s.hunger == 0
