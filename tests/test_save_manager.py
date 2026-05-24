"""Tests for SaveManager — serialization helpers and full save/load round-trips."""
from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from classes.entity import Entity
from classes.game import Game
from classes.item import Equipment, Item
from classes.save_manager import SaveManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_minimal_map(game: Game) -> None:
    """Identical to conftest version — copied here to avoid circular imports."""
    h, w = 10, 20
    game.map = [['#'] * w for _ in range(h)]
    for y in range(2, 7):
        for x in range(2, 12):
            game.map[y][x] = '.'
    game.rooms = [(2, 2, 10, 5)]
    game.height = h
    game.width = w
    game.visible = [[False] * w for _ in range(h)]
    game.explored = [[False] * w for _ in range(h)]
    game.stairs_up_x, game.stairs_up_y = 3, 3
    game.stairs_x, game.stairs_y = 10, 4
    game.player.x, game.player.y = 5, 4
    from classes.map_generator import MapGenerator
    mg = MapGenerator(24, 80)
    mg.height = h
    mg.width = w
    game.map_generator = mg


def make_save_game(mock_stdscr: MagicMock) -> Game:
    game = Game.create_minimal(24, 80, mock_stdscr)
    _apply_minimal_map(game)
    return game


# ---------------------------------------------------------------------------
# Internal serialization helpers
# ---------------------------------------------------------------------------

class TestSerializeMap:
    def test_round_trip(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        original = [['#', '.', '#'], ['.', '.', '.']]
        serialized = sm._serialize_map(original)  # type: ignore[reportPrivateUsage]
        restored = sm._deserialize_map(serialized)  # type: ignore[reportPrivateUsage]
        assert restored == original

    def test_empty_map_round_trip(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        assert sm._serialize_map([]) == ""  # type: ignore[reportPrivateUsage]
        assert sm._deserialize_map("") == []  # type: ignore[reportPrivateUsage]


class TestSerialize2DArray:
    def test_boolean_round_trip(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        original = [[True, False, True], [False, True, False]]
        serialized = sm._serialize_2d_array(original)  # type: ignore[reportPrivateUsage]
        restored = sm._deserialize_2d_array(serialized, width=3, height=2)  # type: ignore[reportPrivateUsage]
        assert restored == original

    def test_empty_array(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        assert sm._serialize_2d_array([]) == ""  # type: ignore[reportPrivateUsage]


class TestSerializeInventory:
    def test_round_trip_with_consumable(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        fn: Callable[[Entity], Any] = lambda e: e.heal(20)
        potion = Item('Red Potion', fn,
                      value=20, effect_type='heal', gold_value=50)
        inv: Counter[Item] = Counter({potion: 3})
        serialized = sm._serialize_inventory(inv)  # type: ignore[reportPrivateUsage]
        restored = sm._deserialize_inventory(serialized)  # type: ignore[reportPrivateUsage]
        names = {item.name: count for item, count in restored.items()}
        assert names.get('Red Potion') == 3

    def test_round_trip_with_equipment(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        sword = Equipment('Iron Sword', 'weapon', 'hands', 5,
                          damage={'min': 1, 'max': 6})
        inv: Counter[Item] = Counter({sword: 1})
        serialized = sm._serialize_inventory(inv)  # type: ignore[reportPrivateUsage]
        restored = sm._deserialize_inventory(serialized)  # type: ignore[reportPrivateUsage]
        names = {item.name for item in restored}
        assert 'Iron Sword' in names


class TestSerializeEquipment:
    def test_empty_slots_round_trip(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        entity = Entity(0, 0, '@', 'P', 100, 0, 0)
        serialized = sm._serialize_equipment(entity.equipment)  # type: ignore[reportPrivateUsage]
        restored = sm._deserialize_equipment(serialized)  # type: ignore[reportPrivateUsage]
        # All slots should still exist with item=None
        assert 'a' in restored
        assert restored['a']['item'] is None

    def test_equipped_item_round_trip(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        entity = Entity(0, 0, '@', 'P', 100, 0, 0)
        sword = Equipment('Steel Sword', 'weapon', 'hands', 8,
                          damage={'min': 2, 'max': 8})
        entity.equip_item(sword)
        serialized = sm._serialize_equipment(entity.equipment)  # type: ignore[reportPrivateUsage]
        restored = sm._deserialize_equipment(serialized)  # type: ignore[reportPrivateUsage]
        assert restored['a']['item'] is not None
        assert restored['a']['item'].name == 'Steel Sword'


# ---------------------------------------------------------------------------
# save_game / load_game
# ---------------------------------------------------------------------------

class TestSaveGame:
    def test_creates_save_file(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        game = make_save_game(mock_stdscr)
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, slot=1)
        assert (tmp_path / 'save_1.json').exists()

    def test_save_file_is_valid_json(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        game = make_save_game(mock_stdscr)
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, slot=1)
        with open(tmp_path / 'save_1.json') as f:
            data = json.load(f)
        assert 'character_name' in data
        assert 'player' in data
        assert 'game_state' in data

    def test_invalid_slot_raises(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        game = make_save_game(mock_stdscr)
        sm = SaveManager(save_dir=str(tmp_path))
        with pytest.raises(ValueError):
            sm.save_game(game, slot=0)
        with pytest.raises(ValueError):
            sm.save_game(game, slot=11)


class TestLoadGame:
    def _save_and_load(
        self,
        tmp_path: Path,
        mock_stdscr: MagicMock,
        mutate: Callable[[Game], None] | None = None,
    ) -> tuple[Game, Game]:
        """Save a game, optionally mutate it, then load into a fresh instance."""
        save_game = make_save_game(mock_stdscr)
        if mutate:
            mutate(save_game)
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(save_game, slot=1)
        load_game = Game.create_minimal(24, 80, mock_stdscr)
        sm.load_game(load_game, slot=1)
        return save_game, load_game

    def test_player_name_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None: g.player.name = 'Percival'
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        assert loaded.player.name == 'Percival'

    def test_player_stats_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None:
            g.player.strength = 18
            g.player.dexterity = 14
            g.player.level = 5
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        assert loaded.player.strength == 18
        assert loaded.player.dexterity == 14
        assert loaded.player.level == 5

    def test_player_health_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None:
            g.player.max_health = 150.0
            g.player.health = 87.0
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        assert loaded.player.max_health == 150.0
        assert loaded.player.health == 87.0

    def test_player_position_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        _, loaded = self._save_and_load(tmp_path, mock_stdscr)
        assert loaded.player.x == 5
        assert loaded.player.y == 4

    def test_player_money_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None: g.player.money = 1234
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        assert loaded.player.money == 1234

    def test_dungeon_level_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None: g.dungeon_level = 7
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        assert loaded.dungeon_level == 7

    def test_turn_count_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None: g.turn_count = 314
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        assert loaded.turn_count == 314

    def test_map_content_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        _, loaded = self._save_and_load(tmp_path, mock_stdscr)
        # Room tiles should be floor, borders should be walls
        assert loaded.map[4][5] == '.'
        assert loaded.map[0][0] == '#'

    def test_rooms_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        _, loaded = self._save_and_load(tmp_path, mock_stdscr)
        assert loaded.rooms == [(2, 2, 10, 5)]

    def test_inventory_count_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        from classes.item_loader import all_consumables
        def mutate(g: Game) -> None:
            hp = next(i for i in all_consumables if i.name == 'Health Potion')
            g.player.inventory.clear()
            g.player.add_item(hp)
            g.player.add_item(hp)
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        hp_in_inv = next((i for i in loaded.player.inventory
                          if i.name == 'Health Potion'), None)
        assert hp_in_inv is not None
        assert loaded.player.inventory[hp_in_inv] == 2

    def test_equipped_weapon_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None:
            sword = Equipment('Saved Sword', 'weapon', 'hands', 7,
                              damage={'min': 2, 'max': 8})
            g.player.equipment['a']['item'] = None
            g.player.equip_item(sword)
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        assert loaded.player.equipment['a']['item'] is not None
        assert loaded.player.equipment['a']['item'].name == 'Saved Sword'

    def test_enemy_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None:
            enemy = Entity(3, 4, 'E', 'Saved Goblin', 25.0, 0, 0)
            enemy.health = 18.0
            g.enemies.append(enemy)
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        assert len(loaded.enemies) == 1
        assert loaded.enemies[0].name == 'Saved Goblin'
        assert loaded.enemies[0].health == 18.0
        assert loaded.enemies[0].x == 3

    def test_messages_last_10_preserved(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        def mutate(g: Game) -> None:
            g.messages = [f'msg{i}' for i in range(15)]
        _, loaded = self._save_and_load(tmp_path, mock_stdscr, mutate)
        # Only last 10 are saved
        assert len(loaded.messages) <= 10
        assert 'msg14' in loaded.messages

    def test_load_nonexistent_slot_raises(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        game = Game.create_minimal(24, 80, mock_stdscr)
        with pytest.raises(FileNotFoundError):
            sm.load_game(game, slot=5)

    def test_load_invalid_slot_raises(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        game = Game.create_minimal(24, 80, mock_stdscr)
        with pytest.raises(ValueError):
            sm.load_game(game, slot=0)


# ---------------------------------------------------------------------------
# delete_save / get_save_info
# ---------------------------------------------------------------------------

class TestDeleteSave:
    def test_delete_removes_file(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        game = make_save_game(mock_stdscr)
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, slot=2)
        assert (tmp_path / 'save_2.json').exists()
        sm.delete_save(slot=2)
        assert not (tmp_path / 'save_2.json').exists()

    def test_delete_returns_true_when_exists(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        game = make_save_game(mock_stdscr)
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, slot=3)
        assert sm.delete_save(slot=3) is True

    def test_delete_returns_false_when_absent(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        assert sm.delete_save(slot=4) is False

    def test_delete_invalid_slot_raises(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        with pytest.raises(ValueError):
            sm.delete_save(slot=0)


class TestGetSaveInfo:
    def test_empty_slot_reports_not_exists(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        info = sm.get_save_info(slot=1)
        assert info['exists'] is False

    def test_filled_slot_reports_exists(self, tmp_path: Path, mock_stdscr: MagicMock) -> None:
        game = make_save_game(mock_stdscr)
        game.player.name = 'Aldric'
        game.player.level = 3
        game.dungeon_level = 2
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, slot=1)
        info = sm.get_save_info(slot=1)
        assert info['exists'] is True
        assert info['character_name'] == 'Aldric'
        assert info['player_level'] == 3
        assert info['level'] == 2

    def test_get_all_save_info_returns_10_entries(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        infos = sm.get_all_save_info()
        assert len(infos) == 10

    def test_get_all_save_info_slot_numbers(self, tmp_path: Path) -> None:
        sm = SaveManager(save_dir=str(tmp_path))
        infos = sm.get_all_save_info()
        slots = [info['slot'] for info in infos]
        assert slots == list(range(1, 11))
