"""Tests for item_loader.py — material/item loading and every effect type."""
import pytest

from classes.entity import Entity
from classes.item_loader import (
    Material,
    create_effect,
    load_items,
    load_materials,
)


@pytest.fixture
def player():
    e = Entity(0, 0, '@', 'TestPlayer', 100, 0, 0)
    e.mana = 5.0
    e.max_mana = 20.0
    e.hunger = 80
    e.poisoned = True
    return e


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

class TestLoadMaterials:
    def test_returns_non_empty_list(self):
        mats = load_materials()
        assert len(mats) > 0

    def test_all_items_are_material_instances(self):
        mats = load_materials()
        assert all(isinstance(m, Material) for m in mats)

    def test_each_material_has_name_and_power(self):
        for m in load_materials():
            assert isinstance(m.name, str) and m.name
            assert isinstance(m.power, (int, float)) and m.power > 0

    def test_value_multiplier_equals_power(self):
        for m in load_materials():
            assert m.value_multiplier == m.power

    def test_materials_span_power_range(self):
        powers = [m.power for m in load_materials()]
        assert min(powers) >= 1
        assert max(powers) >= 10


class TestMaterialClass:
    def test_constructor(self):
        m = Material('Adamantine', 18)
        assert m.name == 'Adamantine'
        assert m.power == 18
        assert m.value_multiplier == 18


# ---------------------------------------------------------------------------
# Item loading
# ---------------------------------------------------------------------------

class TestLoadItems:
    def test_returns_five_element_tuple(self):
        result = load_items()
        assert len(result) == 5

    def test_consumables_non_empty(self):
        consumables, *_ = load_items()
        assert len(consumables) > 0

    def test_equipment_non_empty(self):
        _, equipment, *_ = load_items()
        assert len(equipment) > 0

    def test_all_items_non_empty(self):
        *_, all_items = load_items()
        assert len(all_items) > 0

    def test_all_items_is_union(self):
        consumables, equipment, misc, _, all_items = load_items()
        assert len(all_items) >= len(consumables) + len(equipment)

    def test_consumables_have_effect_callable(self):
        consumables, *_ = load_items()
        for item in consumables:
            assert callable(item.effect), f"{item.name} missing callable effect"

    def test_equipment_has_slot(self):
        _, equipment, *_ = load_items()
        for item in equipment:
            assert item.slot, f"{item.name} missing slot"


# ---------------------------------------------------------------------------
# create_effect — one test per supported effect type
# ---------------------------------------------------------------------------

class TestCreateEffectHeal:
    def test_heals_entity(self, player):
        player.health = 50.0
        player.max_health = 100.0
        effect = create_effect('heal', 30, None)
        effect(player)
        assert player.health == 80.0

    def test_does_not_exceed_max_health(self, player):
        player.health = 90.0
        player.max_health = 100.0
        effect = create_effect('heal', 50, None)
        effect(player)
        assert player.health == 100.0


class TestCreateEffectRestoreMana:
    def test_restores_mana(self, player):
        effect = create_effect('restore_mana', 8, None)
        effect(player)
        assert player.mana == min(13.0, player.max_mana)

    def test_does_not_exceed_max_mana(self, player):
        player.mana = 18.0
        effect = create_effect('restore_mana', 10, None)
        effect(player)
        assert player.mana == player.max_mana


class TestCreateEffectBoostStrength:
    def test_adds_strength_boost(self, player):
        effect = create_effect('boost_strength', 5, 10)
        effect(player)
        assert 'strength' in player.status_comp.boosts
        assert player.status_comp.boosts['strength']['value'] == 5
        assert player.status_comp.boosts['strength']['duration'] == 10

    def test_get_stat_includes_boost(self, player):
        base = player.strength
        effect = create_effect('boost_strength', 4, 5)
        effect(player)
        assert player.get_stat('strength') == base + 4


class TestCreateEffectBoostDexterity:
    def test_adds_dexterity_boost(self, player):
        effect = create_effect('boost_dexterity', 3, 8)
        effect(player)
        assert player.status_comp.boosts['dexterity']['value'] == 3


class TestCreateEffectBoostConstitution:
    def test_adds_constitution_boost(self, player):
        effect = create_effect('boost_constitution', 2, 5)
        effect(player)
        assert 'constitution' in player.status_comp.boosts


class TestCreateEffectBoostIntelligence:
    def test_adds_intelligence_boost(self, player):
        effect = create_effect('boost_intelligence', 6, 12)
        effect(player)
        assert 'intelligence' in player.status_comp.boosts


class TestCreateEffectBoostSpeed:
    def test_adds_speed_boost(self, player):
        effect = create_effect('boost_speed', 10, 5)
        effect(player)
        assert 'speed' in player.status_comp.boosts


class TestCreateEffectBoostCharisma:
    def test_adds_charisma_boost(self, player):
        effect = create_effect('boost_charisma', 3, 6)
        effect(player)
        assert 'charisma' in player.status_comp.boosts


class TestCreateEffectCurePoison:
    def test_clears_poisoned_flag(self, player):
        assert player.poisoned is True
        effect = create_effect('cure_poison', None, None)
        effect(player)
        assert player.poisoned is False

    def test_message_when_not_poisoned(self, player):
        player.poisoned = False
        effect = create_effect('cure_poison', None, None)
        result = effect(player)
        assert 'not poisoned' in result.lower()


class TestCreateEffectSatiate:
    def test_reduces_hunger(self, player):
        player.hunger = 80
        effect = create_effect('satiate', 30, None)
        effect(player)
        assert player.hunger == 50

    def test_hunger_floor_is_zero(self, player):
        player.hunger = 10
        effect = create_effect('satiate', 50, None)
        effect(player)
        assert player.hunger == 0


class TestCreateEffectIdentify:
    def test_returns_string(self, player):
        effect = create_effect('identify', None, None)
        result = effect(player)
        assert isinstance(result, str)


class TestCreateEffectDetectMagic:
    def test_returns_string(self, player):
        effect = create_effect('detect_magic', None, None)
        result = effect(player)
        assert isinstance(result, str)


class TestCreateEffectLight:
    def test_returns_string(self, player):
        effect = create_effect('light', None, None)
        result = effect(player)
        assert isinstance(result, str)


class TestCreateEffectPoison:
    def test_reduces_health(self, player):
        player.health = 80.0
        effect = create_effect('poison', 15, None)
        effect(player)
        assert player.health == 65.0

    def test_health_floors_at_zero(self, player):
        player.health = 5.0
        effect = create_effect('poison', 100, None)
        effect(player)
        assert player.health == 0.0


class TestCreateEffectDamage:
    def test_reduces_health(self, player):
        player.health = 100.0
        effect = create_effect('damage', 25, None)
        effect(player)
        assert player.health == 75.0


class TestCreateEffectUnknown:
    def test_returns_error_string(self, player):
        effect = create_effect('nonexistent_effect', 10, 5)
        result = effect(player)
        assert isinstance(result, str)
        assert 'nonexistent_effect' in result
