"""Tests for monster_loader.py — template loading and loot creation."""
import random

import pytest

from classes.item import Equipment, Item
from classes.monster_loader import MonsterTemplate, load_monsters


@pytest.fixture(autouse=True)
def seed_random():
    random.seed(42)


class TestLoadMonsters:
    def test_returns_non_empty_list(self):
        monsters = load_monsters()
        assert len(monsters) > 0

    def test_all_items_are_monster_templates(self):
        monsters = load_monsters()
        assert all(isinstance(m, MonsterTemplate) for m in monsters)

    def test_each_template_has_required_fields(self):
        for m in load_monsters():
            assert isinstance(m.name, str) and m.name, f"Missing name: {m}"
            assert isinstance(m.xp, (int, float)), f"Bad xp: {m.name}"
            assert isinstance(m.gold, (int, float)), f"Bad gold: {m.name}"
            assert isinstance(m.item_names, list), f"Bad items: {m.name}"
            assert isinstance(m.challenge_rating, (int, float)), f"Bad CR: {m.name}"
            assert isinstance(m.archetype, str), f"Bad archetype: {m.name}"

    def test_challenge_ratings_are_positive(self):
        for m in load_monsters():
            assert m.challenge_rating > 0, f"{m.name} has non-positive CR"

    def test_xp_rewards_are_non_negative(self):
        for m in load_monsters():
            assert m.xp >= 0, f"{m.name} has negative XP"

    def test_archetypes_are_known_strings(self):
        known = {'humanoid', 'animal', 'undead', 'construct', 'abomination',
                 'unknown'}
        for m in load_monsters():
            assert m.archetype in known, f"Unexpected archetype: {m.archetype}"


class TestMonsterTemplateLoot:
    def test_create_loot_returns_list(self):
        monsters = load_monsters()
        for m in monsters:
            loot = m.create_loot()
            assert isinstance(loot, list), f"{m.name}.create_loot() not a list"

    def test_no_items_produces_empty_loot(self):
        template = MonsterTemplate('Ghost', 50, 0, [], 1.0, 'undead')
        assert template.create_loot() == []

    def test_equipment_loot_gets_material_applied(self):
        # Use a monster whose loot list contains a known equipment item name.
        # If any loaded monster has an equipment item in loot, verify material name.
        monsters = [m for m in load_monsters() if m.item_names]
        if not monsters:
            pytest.skip("No monsters with loot defined")

        random.seed(0)
        for m in monsters:
            loot = m.create_loot()
            for item in loot:
                if isinstance(item, Equipment):
                    # Equipment should have a material name prepended
                    assert ' ' in item.name, f"No material in name: {item.name}"
                    assert item.material_type is not None
                    break
            else:
                continue
            break

    def test_consumable_loot_is_item_not_equipment(self):
        monsters = load_monsters()
        for m in monsters:
            loot = m.create_loot()
            for item in loot:
                if not isinstance(item, Equipment):
                    # Non-equipment loot should be an Item
                    assert isinstance(item, Item)
                    break

    def test_unknown_item_name_produces_placeholder(self):
        template = MonsterTemplate('Ghost', 0, 0, ['NonexistentItem999'], 1.0, 'undead')
        loot = template.create_loot()
        assert len(loot) == 1
        assert loot[0].name == 'NonexistentItem999'
