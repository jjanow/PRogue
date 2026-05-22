"""Tests for Item and Equipment classes in classes/item.py."""
import pytest

from classes.item import Equipment, Item


def _make_item(name='Health Potion', effect_type='heal', value=20):
    effect = lambda e: e.heal(value)
    return Item(
        name=name,
        effect=effect,
        duration=None,
        value=value,
        weight=1,
        effect_type=effect_type,
        gold_value=50,
        material_type='potion',
    )


def _make_weapon(name='Iron Dagger', stat_boost=5):
    return Equipment(
        name=name,
        slot='weapon',
        body_part='hands',
        stat_boost=stat_boost,
        damage={'min': 1, 'max': 4},
        ac=0,
        accuracy_bonus=2,
        weight=1,
        material_type='Iron',
        gold_value=100,
    )


def _make_armor(name='Iron Breastplate', stat_boost=4, ac=3):
    return Equipment(
        name=name,
        slot='armor',
        body_part='torso',
        stat_boost=stat_boost,
        damage=None,
        ac=ac,
        accuracy_bonus=0,
        weight=5,
        material_type='Iron',
        gold_value=150,
    )


class TestItemEquality:
    def test_items_equal_by_name(self):
        a = _make_item('Health Potion')
        b = _make_item('Health Potion')
        assert a == b

    def test_items_unequal_different_name(self):
        a = _make_item('Health Potion')
        b = _make_item('Mana Potion')
        assert a != b

    def test_hash_consistent_with_name(self):
        a = _make_item('Health Potion')
        b = _make_item('Health Potion')
        assert hash(a) == hash(b)

    def test_inequality_with_non_item(self):
        item = _make_item()
        assert item != 'Health Potion'
        assert item != 42


class TestItemAttributes:
    def test_default_position_is_none(self):
        item = _make_item()
        assert item.x is None
        assert item.y is None

    def test_default_quantity_is_one(self):
        item = _make_item()
        assert item.quantity == 1

    def test_default_seen_is_false(self):
        item = _make_item()
        assert item.seen is False

    def test_stores_all_fields(self):
        item = _make_item('Elixir', 'heal', 50)
        assert item.name == 'Elixir'
        assert item.value == 50
        assert item.weight == 1
        assert item.effect_type == 'heal'
        assert item.gold_value == 50
        assert item.material_type == 'potion'


class TestItemSerialization:
    def test_to_dict_contains_expected_keys(self):
        item = _make_item()
        d = item.to_dict()
        for key in ('name', 'duration', 'value', 'weight', 'effect_type',
                    'gold_value', 'material_type', 'x', 'y', 'quantity', 'seen'):
            assert key in d, f"Missing key: {key}"

    def test_to_dict_name(self):
        item = _make_item('Super Potion')
        assert item.to_dict()['name'] == 'Super Potion'

    def test_to_dict_preserves_position(self):
        item = _make_item()
        item.x, item.y = 10, 15
        d = item.to_dict()
        assert d['x'] == 10
        assert d['y'] == 15

    def test_to_dict_preserves_seen(self):
        item = _make_item()
        item.seen = True
        assert item.to_dict()['seen'] is True

    def test_from_dict_round_trip(self):
        item = _make_item('Round Potion', 'heal', 30)
        item.x, item.y = 7, 3
        item.seen = True
        d = item.to_dict()
        restored = Item.from_dict(d)
        assert restored.name == item.name
        assert restored.value == item.value
        assert restored.x == item.x
        assert restored.y == item.y
        assert restored.seen is True

    def test_from_dict_effect_type_produces_callable(self):
        item = _make_item('Healable', 'heal', 20)
        d = item.to_dict()
        restored = Item.from_dict(d)
        assert callable(restored.effect)


class TestEquipmentSlotBonuses:
    def test_weapon_slot_damage_bonus_equals_stat_boost(self):
        w = _make_weapon(stat_boost=7)
        assert w.damage_bonus == 7
        assert w.defense_bonus == 0

    def test_missile_weapon_slot_also_damage_bonus(self):
        bow = Equipment('Iron Bow', 'missile weapon', 'hands', 6, damage={'min': 1, 'max': 6})
        assert bow.damage_bonus == 6
        assert bow.defense_bonus == 0

    def test_armor_slot_defense_bonus_equals_stat_boost(self):
        a = _make_armor(stat_boost=4)
        assert a.defense_bonus == 4
        assert a.damage_bonus == 0

    def test_helmet_slot_defense_bonus(self):
        helm = Equipment('Iron Helm', 'helmet', 'head', 3, ac=1)
        assert helm.defense_bonus == 3
        assert helm.damage_bonus == 0

    def test_ac_stored_correctly(self):
        a = _make_armor(ac=5)
        assert a.ac == 5

    def test_ac_defaults_to_zero_when_none(self):
        w = Equipment('Iron Sword', 'weapon', 'hands', 4, ac=None)
        assert w.ac == 0

    def test_accuracy_bonus_stored(self):
        w = _make_weapon()
        assert w.accuracy_bonus == 2


class TestEquipmentSerialization:
    def test_to_dict_includes_equipment_fields(self):
        w = _make_weapon()
        d = w.to_dict()
        for key in ('slot', 'body_part', 'damage', 'ac', 'stat_boost',
                    'damage_bonus', 'defense_bonus', 'accuracy_bonus'):
            assert key in d, f"Missing key: {key}"

    def test_to_dict_round_trip_weapon(self):
        w = _make_weapon('Crude Dagger', stat_boost=1)
        w.x, w.y = 3, 8
        d = w.to_dict()
        restored = Equipment.from_dict(d)
        assert restored.name == w.name
        assert restored.slot == w.slot
        assert restored.stat_boost == w.stat_boost
        assert restored.damage_bonus == w.damage_bonus
        assert restored.defense_bonus == w.defense_bonus
        assert restored.accuracy_bonus == w.accuracy_bonus
        assert restored.x == w.x
        assert restored.y == w.y

    def test_to_dict_round_trip_armor(self):
        a = _make_armor('Steel Plate', stat_boost=8, ac=4)
        d = a.to_dict()
        restored = Equipment.from_dict(d)
        assert restored.slot == 'armor'
        assert restored.ac == 4
        assert restored.defense_bonus == 8
        assert restored.damage_bonus == 0
