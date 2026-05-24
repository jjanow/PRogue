"""Tests for Entity — combat properties, inventory, equipment, progression, status."""
from __future__ import annotations
import random
from typing import Callable

from classes.entity import Entity
from classes.item import Equipment, Item


def make_entity(x: int = 0, y: int = 0, char: str = '@', name: str = 'Hero',
                health: float = 100, damage: float = 0, defense: float = 0) -> Entity:
    return Entity(x, y, char, name, float(health), float(damage), float(defense))


def make_weapon(name: str = 'Iron Sword', slot: str = 'weapon', stat_boost: float = 5,
                damage: dict[str, int] | int | None = None, ac: int = 0, accuracy: float = 0) -> Equipment:
    if damage is None:
        damage = {'min': 2, 'max': 6}
    return Equipment(name, slot, 'hands', stat_boost,
                     damage=damage, ac=ac, accuracy_bonus=accuracy)


def make_armor(name: str = 'Iron Breastplate', slot: str = 'armor', stat_boost: float = 4, ac: int = 3) -> Equipment:
    return Equipment(name, slot, 'torso', stat_boost, damage=None, ac=ac)


def make_potion(name: str = 'Test Potion', heal_amount: float = 20) -> Item:
    fn: Callable[[Entity], str] = lambda e: e.heal(heal_amount)
    return Item(name, fn, value=heal_amount, effect_type='heal')


class TestEntityProperties:
    def test_position_delegates(self) -> None:
        e = make_entity(3, 7)
        assert e.x == 3
        assert e.y == 7
        e.x, e.y = 10, 20
        assert e.position.x == 10
        assert e.position.y == 20

    def test_health_delegates(self) -> None:
        e = make_entity(health=80)
        assert e.health == 80.0
        e.health = 50.0
        assert e.health_comp.health == 50.0

    def test_stats_delegate(self) -> None:
        e = make_entity()
        e.strength = 15
        assert e.stats.strength == 15
        assert e.strength == 15

    def test_name_delegates(self) -> None:
        e = make_entity(name='Alice')
        assert e.name == 'Alice'
        e.name = 'Bob'
        assert e.char_info.name == 'Bob'

    def test_money_delegates(self) -> None:
        e = make_entity()
        e.money = 500
        assert e.money_comp.money == 500


class TestEquipmentSlots:
    def test_has_13_slots(self) -> None:
        e = make_entity()
        assert len(e.equipment) == 13

    def test_slot_names_cover_expected_gear(self) -> None:
        e = make_entity()
        names = {v['name'] for v in e.equipment.values()}
        for expected in ('weapon', 'missile weapon', 'helmet', 'amulet', 'shield',
                         'armor', 'cloak', 'girdle', 'gauntlets', 'boots',
                         'ring (right)', 'ring (left)', 'bracers'):
            assert expected in names


class TestDamageProperty:
    def test_no_weapon_no_base(self) -> None:
        e = make_entity()
        e.strength = 10
        e.level = 1
        e.base_damage = 0.0
        assert e.damage == 5.5

    def test_weapon_damage_bonus_added(self) -> None:
        e = make_entity()
        e.strength = 10
        e.level = 1
        e.base_damage = 0.0
        weapon = make_weapon(stat_boost=10)
        e.equip_item(weapon)
        assert e.damage == 15.5

    def test_strength_scales_damage(self) -> None:
        e = make_entity()
        e.strength = 20
        e.level = 1
        e.base_damage = 0.0
        assert e.damage == 10.5


class TestDefenseProperty:
    def test_no_armor_no_base(self) -> None:
        e = make_entity()
        e.dexterity = 10
        e.constitution = 10
        e.level = 1
        e.base_defense = 0.0
        assert e.defense == 5.5

    def test_armor_defense_bonus_added(self) -> None:
        e = make_entity()
        e.dexterity = 10
        e.constitution = 10
        e.level = 1
        e.base_defense = 0.0
        armor = make_armor(stat_boost=6)
        e.equip_item(armor)
        assert e.defense == 11.5

    def test_level_bonus_adds_half_per_level(self) -> None:
        e = make_entity()
        e.dexterity = 0
        e.constitution = 0
        e.base_defense = 0.0
        e.level = 4
        assert e.defense == 2.0


class TestArmorProperty:
    def test_no_equipment_returns_zero(self) -> None:
        e = make_entity()
        assert e.armor == 0

    def test_armor_ac_summed(self) -> None:
        e = make_entity()
        a = make_armor(ac=4)
        e.equip_item(a)
        assert e.armor == 4

    def test_multiple_armor_pieces_summed(self) -> None:
        e = make_entity()
        helm = Equipment('Helm', 'helmet', 'head', 2, ac=1)
        boots = Equipment('Boots', 'boots', 'feet', 1, ac=1)
        e.equip_item(helm)
        e.equip_item(boots)
        assert e.armor == 2


class TestHeal:
    def test_heals_by_amount(self) -> None:
        e = make_entity(health=100)
        e.health = 60.0
        result = e.heal(20)
        assert e.health == 80.0
        assert '20' in result

    def test_capped_at_max_health(self) -> None:
        e = make_entity(health=100)
        e.health = 90.0
        e.heal(50)
        assert e.health == 100.0

    def test_full_health_returns_message(self) -> None:
        e = make_entity(health=100)
        e.health = 100.0
        result = e.heal(10)
        assert 'full' in result.lower()


class TestTakeDamage:
    def test_reduces_health(self) -> None:
        e = make_entity(health=100)
        e.take_damage(30)
        assert e.health == 70.0

    def test_clamps_to_zero(self) -> None:
        e = make_entity(health=100)
        e.health = 10.0
        e.take_damage(999)
        assert e.health == 0.0


class TestRestoreMana:
    def test_restores_mana(self) -> None:
        e = make_entity()
        e.mana = 3.0
        e.max_mana = 10.0
        e.restore_mana(5)
        assert e.mana == 8.0

    def test_capped_at_max_mana(self) -> None:
        e = make_entity()
        e.mana = 8.0
        e.max_mana = 10.0
        e.restore_mana(100)
        assert e.mana == 10.0


class TestAddItem:
    def test_new_item_count_is_one(self) -> None:
        e = make_entity()
        potion = make_potion()
        e.add_item(potion)
        assert e.inventory[potion] == 1

    def test_stacks_same_name(self) -> None:
        e = make_entity()
        p1 = make_potion('Potion')
        p2 = make_potion('Potion')
        e.add_item(p1)
        e.add_item(p2)
        key = next(i for i in e.inventory if i.name == 'Potion')
        assert e.inventory[key] == 2

    def test_different_names_separate_stacks(self) -> None:
        e = make_entity()
        e.add_item(make_potion('A'))
        e.add_item(make_potion('B'))
        assert len(e.inventory) == 2


class TestRemoveItem:
    def test_decrements_count(self) -> None:
        e = make_entity()
        potion = make_potion()
        e.add_item(potion)
        e.add_item(potion)
        e.remove_item(potion)
        key = next(i for i in e.inventory if i.name == potion.name)
        assert e.inventory[key] == 1

    def test_removes_key_at_zero(self) -> None:
        e = make_entity()
        potion = make_potion()
        e.add_item(potion)
        e.remove_item(potion)
        assert not any(i.name == potion.name for i in e.inventory)

    def test_returns_true_on_success(self) -> None:
        e = make_entity()
        potion = make_potion()
        e.add_item(potion)
        assert e.remove_item(potion) is True

    def test_returns_false_when_not_present(self) -> None:
        e = make_entity()
        potion = make_potion()
        assert e.remove_item(potion) is False


class TestGetInventoryItems:
    def test_returns_list_of_tuples(self) -> None:
        e = make_entity()
        e.add_item(make_potion())
        items = e.get_inventory_items()
        assert isinstance(items, list)
        assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in items)


class TestEquipMethod:
    def test_equip_weapon_in_slot_a(self) -> None:
        e = make_entity()
        w = make_weapon()
        e.add_item(w)
        result = e.equip(w, 'a')
        assert 'Equipped' in result
        assert e.equipment['a']['item'] is w

    def test_equip_removes_from_inventory(self) -> None:
        e = make_entity()
        w = make_weapon()
        e.add_item(w)
        e.equip(w, 'a')
        assert not any(i.name == w.name for i in e.inventory)

    def test_equip_returns_old_item_to_inventory(self) -> None:
        e = make_entity()
        w1 = make_weapon('Old Sword')
        w2 = make_weapon('New Sword')
        e.add_item(w1)
        e.equip(w1, 'a')
        e.add_item(w2)
        e.equip(w2, 'a')
        assert any(i.name == 'Old Sword' for i in e.inventory)

    def test_equip_wrong_slot_fails(self) -> None:
        e = make_entity()
        w = make_weapon(slot='weapon')
        e.add_item(w)
        result = e.equip(w, 'f')
        assert 'Cannot' in result
        assert e.equipment['f']['item'] is None


class TestEquipItemMethod:
    def test_equips_from_inventory(self) -> None:
        e = make_entity()
        a = make_armor()
        e.add_item(a)
        e.equip_item(a)
        assert e.equipment['f']['item'] is a

    def test_swaps_with_existing(self) -> None:
        e = make_entity()
        a1 = make_armor('Old Armor')
        a2 = make_armor('New Armor')
        e.add_item(a1)
        e.equip_item(a1)
        e.add_item(a2)
        e.equip_item(a2)
        assert e.equipment['f']['item'] is not None
        assert e.equipment['f']['item'].name == 'New Armor'
        assert any(i.name == 'Old Armor' for i in e.inventory)


class TestUnequipItem:
    def test_moves_item_to_inventory(self) -> None:
        e = make_entity()
        w = make_weapon()
        e.equip_item(w)
        e.unequip_item('a')
        assert e.equipment['a']['item'] is None
        assert any(i.name == w.name for i in e.inventory)

    def test_empty_slot_returns_message(self) -> None:
        e = make_entity()
        result = e.unequip_item('a')
        assert 'No item' in result


class TestGetEquippedItems:
    def test_returns_only_occupied_slots(self) -> None:
        e = make_entity()
        w = make_weapon()
        e.equip_item(w)
        equipped = e.get_equipped_items()
        assert 'a' in equipped
        assert equipped['a'].name == w.name

    def test_empty_slots_not_included(self) -> None:
        e = make_entity()
        equipped = e.get_equipped_items()
        assert len(equipped) == 0


class TestGainXP:
    def test_xp_accumulates(self) -> None:
        e = make_entity()
        e.gain_xp(50)
        assert e.xp == 50

    def test_level_up_at_threshold(self) -> None:
        e = make_entity()
        e.gain_xp(100)
        assert e.level == 2

    def test_multiple_levels_at_once(self) -> None:
        random.seed(42)
        e = make_entity()
        e.gain_xp(250)
        assert e.level >= 2

    def test_xp_carries_over_after_level_up(self) -> None:
        random.seed(42)
        e = make_entity()
        e.gain_xp(150)
        assert e.xp > 0


class TestLevelUp:
    def test_level_increments(self) -> None:
        random.seed(42)
        e = make_entity()
        old_level = e.level
        e.level_up()
        assert e.level == old_level + 1

    def test_max_health_increases_by_10(self) -> None:
        random.seed(42)
        e = make_entity()
        old_max = e.max_health
        e.level_up()
        assert e.max_health == old_max + 10

    def test_health_restored_to_max_on_level_up(self) -> None:
        random.seed(42)
        e = make_entity()
        e.health = 50.0
        e.level_up()
        assert e.health == e.max_health

    def test_all_stats_increase(self) -> None:
        random.seed(42)
        e = make_entity()
        old_stats = {s: getattr(e, s)
                     for s in ('strength', 'dexterity', 'constitution',
                               'intelligence', 'willpower', 'charisma',
                               'appearance', 'perception')}
        e.level_up()
        for stat, old_val in old_stats.items():
            assert getattr(e, stat) >= old_val + 1, f"{stat} not increased"

    def test_speed_increases(self) -> None:
        random.seed(42)
        e = make_entity()
        old_speed = e.speed
        e.level_up()
        assert e.speed >= old_speed + 1


class TestTemporaryBoosts:
    def test_apply_boost_stores_in_comp(self) -> None:
        e = make_entity()
        e.apply_temporary_boost('strength', 5, 10)
        assert e.status_comp.boosts['strength']['value'] == 5
        assert e.status_comp.boosts['strength']['duration'] == 10

    def test_get_stat_returns_base_plus_boost(self) -> None:
        e = make_entity()
        e.strength = 10
        e.apply_temporary_boost('strength', 4, 5)
        assert e.get_stat('strength') == 14

    def test_get_stat_without_boost_returns_base(self) -> None:
        e = make_entity()
        e.strength = 12
        assert e.get_stat('strength') == 12

    def test_update_decrements_duration(self) -> None:
        e = make_entity()
        e.apply_temporary_boost('dexterity', 3, 3)
        e.update_temporary_boosts()
        assert e.status_comp.boosts['dexterity']['duration'] == 2

    def test_expired_boost_removed_and_messaged(self) -> None:
        e = make_entity()
        e.apply_temporary_boost('charisma', 2, 1)
        msgs = e.update_temporary_boosts()
        assert 'charisma' not in e.status_comp.boosts
        assert any('Charisma' in m for m in msgs)


class TestPoison:
    def test_cure_poison_clears_flag(self) -> None:
        e = make_entity()
        e.poisoned = True
        e.cure_poison()
        assert e.poisoned is False

    def test_cure_poison_message_when_not_poisoned(self) -> None:
        e = make_entity()
        e.poisoned = False
        result = e.cure_poison()
        assert 'not poisoned' in result.lower()


class TestSatiate:
    def test_reduces_hunger(self) -> None:
        e = make_entity()
        e.hunger = 60
        e.satiate(20)
        assert e.hunger == 40

    def test_hunger_floors_at_zero(self) -> None:
        e = make_entity()
        e.hunger = 5
        e.satiate(100)
        assert e.hunger == 0


class TestInitializePlayer:
    def test_gives_two_health_potions(self) -> None:
        e = make_entity()
        e.initialize_player()
        hp = next((i for i in e.inventory if i.name == 'Health Potion'), None)
        assert hp is not None
        assert e.inventory[hp] == 2

    def test_equips_weapon_in_slot_a(self) -> None:
        e = make_entity()
        e.initialize_player()
        assert e.equipment['a']['item'] is not None
        assert 'Dagger' in e.equipment['a']['item'].name

    def test_equips_armor_in_slot_f(self) -> None:
        e = make_entity()
        e.initialize_player()
        assert e.equipment['f']['item'] is not None
        assert 'Robe' in e.equipment['f']['item'].name

    def test_starter_items_use_lowest_material(self) -> None:
        e = make_entity()
        e.initialize_player()
        weapon = e.equipment['a']['item']
        assert weapon is not None
        assert weapon.stat_boost == 1
