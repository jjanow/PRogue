"""Tests for StaticMapLoader, town map loading, and town/dungeon transitions."""
import copy
import json
from pathlib import Path

import pytest

from classes.static_map_loader import StaticMapLoader
from classes.item import Item


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TOWN_PATH = Path(__file__).parent.parent / "data" / "maps" / "town.json"


def _make_town_game(mock_stdscr):
    """Return a fully-initialised Game starting in town."""
    from classes.game import Game
    import curses as real_curses
    real_curses.start_color = lambda: None
    real_curses.init_pair = lambda *a: None
    return Game(21, 80, mock_stdscr)


def _apply_dungeon_map(game):
    """Reconfigure a minimal_game into dungeon mode with valid stair positions."""
    game.in_town = False
    game.dungeon_level = 1
    game.stairs_up_x, game.stairs_up_y = 3, 3
    game.stairs_x, game.stairs_y = 10, 4
    game.map[3][3] = '<'
    game.map[4][10] = '>'
    game._town_explored = None
    game._town_items = []


# ---------------------------------------------------------------------------
# StaticMapLoader — format parsing
# ---------------------------------------------------------------------------

class TestStaticMapLoaderBasic:
    def test_loads_map_grid(self, tmp_path):
        data = {
            "tiles": ["###", "#.#", "###"],
            "legend": {},
            "fov_mode": "dungeon"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        grid, _rooms, _spawns, _meta = StaticMapLoader().load(p)
        assert grid[1][1] == '.'
        assert grid[0][0] == '#'

    def test_legend_substitutes_tile_char(self, tmp_path):
        data = {
            "tiles": ["#@#"],
            "legend": {"@": {"tile": "."}},
            "fov_mode": "dungeon"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        grid, _rooms, _spawns, _meta = StaticMapLoader().load(p)
        assert grid[0][1] == '.'

    def test_legend_records_spawn_tag(self, tmp_path):
        data = {
            "tiles": ["#@#"],
            "legend": {"@": {"tile": ".", "tag": "player_start"}},
            "fov_mode": "dungeon"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        _grid, _rooms, spawns, _meta = StaticMapLoader().load(p)
        assert spawns["player_start"] == (1, 0)

    def test_char_without_legend_passes_through(self, tmp_path):
        data = {
            "tiles": ["T"],
            "legend": {},
            "fov_mode": "dungeon"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        grid, _rooms, _spawns, _meta = StaticMapLoader().load(p)
        assert grid[0][0] == 'T'

    def test_short_rows_padded_with_walls(self, tmp_path):
        data = {
            "tiles": ["###", "#."],  # second row is short
            "legend": {},
            "fov_mode": "dungeon"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        grid, _rooms, _spawns, _meta = StaticMapLoader().load(p)
        assert len(grid[0]) == len(grid[1])
        assert grid[1][2] == '#'  # padded with wall

    def test_multiple_spawn_tags(self, tmp_path):
        data = {
            "tiles": ["@.>"],
            "legend": {
                "@": {"tile": ".", "tag": "player_start"},
                ">": {"tile": ">", "tag": "dungeon_entrance"},
            },
            "fov_mode": "dungeon"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        _grid, _rooms, spawns, _meta = StaticMapLoader().load(p)
        assert spawns["player_start"] == (0, 0)
        assert spawns["dungeon_entrance"] == (2, 0)

    def test_auto_detects_stair_down_as_dungeon_entrance(self, tmp_path):
        data = {
            "tiles": [".>"],
            "legend": {},
            "fov_mode": "dungeon"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        _grid, _rooms, spawns, _meta = StaticMapLoader().load(p)
        assert spawns.get("dungeon_entrance") == (1, 0)

    def test_metadata_name_and_fov_mode(self, tmp_path):
        data = {
            "name": "Test Town",
            "fov_mode": "outdoor",
            "tiles": ["##", "#."],
            "legend": {}
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        _grid, _rooms, _spawns, meta = StaticMapLoader().load(p)
        assert meta["name"] == "Test Town"
        assert meta["fov_mode"] == "outdoor"


class TestStaticMapLoaderRooms:
    def test_outdoor_creates_single_interior_room(self, tmp_path):
        data = {
            "tiles": ["####", "#..#", "#..#", "####"],
            "legend": {},
            "fov_mode": "outdoor"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        _grid, rooms, _spawns, _meta = StaticMapLoader().load(p)
        assert len(rooms) == 1
        assert rooms[0] == (1, 1, 2, 2)  # (x, y, w, h) of interior

    def test_dungeon_mode_uses_explicit_rooms(self, tmp_path):
        data = {
            "tiles": ["####", "#..#", "####"],
            "legend": {},
            "fov_mode": "dungeon",
            "rooms": [[1, 1, 2, 1]]
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        _grid, rooms, _spawns, _meta = StaticMapLoader().load(p)
        assert rooms == [(1, 1, 2, 1)]

    def test_dungeon_mode_no_rooms_gives_empty_list(self, tmp_path):
        data = {
            "tiles": ["#.#"],
            "legend": {},
            "fov_mode": "dungeon"
        }
        p = tmp_path / "m.json"
        p.write_text(json.dumps(data))
        _grid, rooms, _spawns, _meta = StaticMapLoader().load(p)
        assert rooms == []


# ---------------------------------------------------------------------------
# Town map file — structure checks
# ---------------------------------------------------------------------------

class TestTownMapFile:
    def test_file_loads_without_error(self):
        grid, rooms, spawns, meta = StaticMapLoader().load(_TOWN_PATH)
        assert grid is not None

    def test_all_rows_same_width(self):
        grid, _r, _s, _m = StaticMapLoader().load(_TOWN_PATH)
        widths = {len(row) for row in grid}
        assert len(widths) == 1

    def test_player_start_spawn_exists(self):
        _grid, _r, spawns, _m = StaticMapLoader().load(_TOWN_PATH)
        assert "player_start" in spawns

    def test_dungeon_entrance_spawn_exists(self):
        _grid, _r, spawns, _m = StaticMapLoader().load(_TOWN_PATH)
        assert "dungeon_entrance" in spawns

    def test_dungeon_entrance_tile_is_stair_down(self):
        grid, _r, spawns, _m = StaticMapLoader().load(_TOWN_PATH)
        ex, ey = spawns["dungeon_entrance"]
        assert grid[ey][ex] == '>'

    def test_player_start_tile_is_floor(self):
        grid, _r, spawns, _m = StaticMapLoader().load(_TOWN_PATH)
        px, py = spawns["player_start"]
        assert grid[py][px] == '.'

    def test_outdoor_fov_mode(self):
        _g, _r, _s, meta = StaticMapLoader().load(_TOWN_PATH)
        assert meta["fov_mode"] == "outdoor"

    def test_outdoor_produces_single_room(self):
        _grid, rooms, _s, _m = StaticMapLoader().load(_TOWN_PATH)
        assert len(rooms) == 1


# ---------------------------------------------------------------------------
# Game initialisation — starts in town
# ---------------------------------------------------------------------------

class TestGameStartsInTown:
    def test_in_town_is_true(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert game.in_town is True

    def test_dungeon_level_is_zero(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert game.dungeon_level == 0

    def test_player_at_player_start(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert (game.player.x, game.player.y) == (24, 7)

    def test_stairs_x_y_is_dungeon_entrance(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert (game.stairs_x, game.stairs_y) == (46, 12)

    def test_no_up_stairs_in_town(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert game.stairs_up_x is None
        assert game.stairs_up_y is None

    def test_no_enemies_in_town(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert len(game.enemies) == 0

    def test_no_items_spawned_in_town(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert len(game.items) == 0

    def test_map_contains_trees(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert any('T' in row for row in game.map)

    def test_trees_are_impassable(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        for y, row in enumerate(game.map):
            for x, tile in enumerate(row):
                if tile == 'T':
                    assert game.is_valid_move(x, y) is False
                    return  # found at least one

    def test_dungeon_entrance_tile_is_valid_move(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        assert game.is_valid_move(game.stairs_x, game.stairs_y) is True


# ---------------------------------------------------------------------------
# use_stairs — town behaviour
# ---------------------------------------------------------------------------

class TestUseStairsTown:
    def test_down_at_entrance_calls_enter_dungeon(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.use_stairs('down')
        assert game.in_town is False
        assert game.dungeon_level == 1

    def test_down_not_at_entrance_does_nothing(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        game.player.x, game.player.y = 5, 5  # somewhere else
        game.use_stairs('down')
        assert game.in_town is True  # no change

    def test_up_in_town_appends_message(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        game.use_stairs('up')
        assert any('no stairs' in m.lower() for m in game.messages)


# ---------------------------------------------------------------------------
# use_stairs — dungeon → town return (level 1 up-stairs)
# ---------------------------------------------------------------------------

class TestUseStairsDungeonReturn:
    def test_up_from_level_1_returns_to_town(self, minimal_game):
        _apply_dungeon_map(minimal_game)
        minimal_game.player.x = minimal_game.stairs_up_x
        minimal_game.player.y = minimal_game.stairs_up_y
        minimal_game.use_stairs('up')
        assert minimal_game.in_town is True

    def test_up_from_level_1_resets_dungeon_level_to_zero(self, minimal_game):
        _apply_dungeon_map(minimal_game)
        minimal_game.player.x = minimal_game.stairs_up_x
        minimal_game.player.y = minimal_game.stairs_up_y
        minimal_game.use_stairs('up')
        assert minimal_game.dungeon_level == 0

    def test_up_from_level_2_goes_to_level_1_not_town(self, minimal_game):
        _apply_dungeon_map(minimal_game)
        minimal_game.dungeon_level = 2
        minimal_game.player.x = minimal_game.stairs_up_x
        minimal_game.player.y = minimal_game.stairs_up_y
        minimal_game.use_stairs('up')
        assert minimal_game.in_town is False
        assert minimal_game.dungeon_level == 1


# ---------------------------------------------------------------------------
# Town FOV cache — explored grid survives dungeon round-trip
# ---------------------------------------------------------------------------

class TestTownExploredCache:
    def test_explored_cache_set_on_enter_dungeon(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        # Mark some tiles explored so there is non-trivial state to cache.
        game.explored[7][24] = True
        game.explored[5][5] = True
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        assert game._town_explored is not None

    def test_cached_explored_is_deep_copy(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        game.explored[3][3] = True
        original_explored = copy.deepcopy(game.explored)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        # Mutate the dungeon explored; the cache must not change.
        game.explored[3][3] = False
        assert game._town_explored[3][3] is True

    def test_explored_restored_on_return_to_town(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        # Explore several tiles, then go to dungeon and back.
        game.explored[7][24] = True
        game.explored[5][10] = True
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        game.return_to_town()
        assert game.explored[7][24] is True
        assert game.explored[5][10] is True

    def test_town_explored_cache_cleared_after_restore(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        game.explored[2][2] = True
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        game.return_to_town()
        assert game._town_explored is None

    def test_fresh_return_without_prior_explore_does_not_crash(self, minimal_game):
        """returning to town with no cached state should work fine."""
        _apply_dungeon_map(minimal_game)
        minimal_game.return_to_town()  # _town_explored is None — no crash


# ---------------------------------------------------------------------------
# Town item cache — items survive dungeon round-trip
# ---------------------------------------------------------------------------

class TestTownItemCache:
    def test_items_cached_on_enter_dungeon(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        sword = Item('Town Sword', lambda e: None)
        sword.x, sword.y = 5, 5
        game.items.append(sword)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        assert any(i.name == 'Town Sword' for i in game._town_items)

    def test_items_cleared_in_dungeon(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        sword = Item('Town Sword', lambda e: None)
        sword.x, sword.y = 5, 5
        game.items.append(sword)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        assert not any(i.name == 'Town Sword' for i in game.items)

    def test_items_restored_on_return_to_town(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        gem = Item('Town Gem', lambda e: None)
        gem.x, gem.y = 8, 8
        game.items.append(gem)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        game.return_to_town()
        assert any(i.name == 'Town Gem' for i in game.items)

    def test_town_item_cache_cleared_after_restore(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        gem = Item('Gem', lambda e: None)
        gem.x, gem.y = 3, 3
        game.items.append(gem)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        game.return_to_town()
        assert game._town_items == []

    def test_dungeon_items_do_not_appear_in_town_on_return(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        # Add a dungeon item directly (simulating a drop/spawn)
        dungeon_item = Item('Dungeon Loot', lambda e: None)
        dungeon_item.x, dungeon_item.y = 3, 3
        game.items.append(dungeon_item)
        game.return_to_town()
        assert not any(i.name == 'Dungeon Loot' for i in game.items)


# ---------------------------------------------------------------------------
# enter_dungeon / return_to_town — message and state checks
# ---------------------------------------------------------------------------

class TestTransitionMessages:
    def test_enter_dungeon_appends_message(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        assert any('dungeon' in m.lower() for m in game.messages)

    def test_return_to_town_appends_message(self, minimal_game):
        _apply_dungeon_map(minimal_game)
        minimal_game.return_to_town()
        assert any('town' in m.lower() or 'millhaven' in m.lower()
                   for m in minimal_game.messages)

    def test_player_placed_at_entrance_on_return(self, mock_stdscr):
        game = _make_town_game(mock_stdscr)
        entrance_x, entrance_y = game.stairs_x, game.stairs_y
        game.player.x, game.player.y = entrance_x, entrance_y
        game.enter_dungeon()
        game.return_to_town()
        assert (game.player.x, game.player.y) == (entrance_x, entrance_y)

    def test_enter_dungeon_clears_enemies(self, mock_stdscr):
        from classes.entity import Entity
        game = _make_town_game(mock_stdscr)
        game.enemies.append(Entity(5, 5, 'E', 'Ghost', 10, 0, 0))
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        # Dungeon generates new enemies; but the ghost we added must be gone
        # (it was cleared before generation).  We just check it's not still there.
        assert not any(e.name == 'Ghost' for e in game.enemies)


# ---------------------------------------------------------------------------
# Save/load round-trips with town state
# ---------------------------------------------------------------------------

class TestSaveLoadTownState:
    def test_in_town_true_survives_save_load(self, tmp_path, mock_stdscr):
        from classes.game import Game
        from classes.save_manager import SaveManager
        game = _make_town_game(mock_stdscr)
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, 1)
        loaded = Game.create_minimal(24, 80, mock_stdscr)
        sm.load_game(loaded, 1)
        assert loaded.in_town is True

    def test_in_town_false_survives_save_load(self, tmp_path, mock_stdscr):
        from classes.game import Game
        from classes.save_manager import SaveManager
        game = _make_town_game(mock_stdscr)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, 1)
        loaded = Game.create_minimal(24, 80, mock_stdscr)
        sm.load_game(loaded, 1)
        assert loaded.in_town is False
        assert loaded.dungeon_level == 1

    def test_town_explored_cache_survives_save_load(self, tmp_path, mock_stdscr):
        from classes.game import Game
        from classes.save_manager import SaveManager
        game = _make_town_game(mock_stdscr)
        # Explore a specific tile, then enter dungeon (caches it).
        game.explored[7][24] = True
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, 1)
        loaded = Game.create_minimal(24, 80, mock_stdscr)
        sm.load_game(loaded, 1)
        assert loaded._town_explored is not None
        assert loaded._town_explored[7][24] is True

    def test_town_items_cache_survives_save_load(self, tmp_path, mock_stdscr):
        from classes.game import Game
        from classes.save_manager import SaveManager
        game = _make_town_game(mock_stdscr)
        gem = Item('Persisted Gem', lambda e: None)
        gem.x, gem.y = 3, 3
        game.items.append(gem)
        game.player.x, game.player.y = game.stairs_x, game.stairs_y
        game.enter_dungeon()
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, 1)
        loaded = Game.create_minimal(24, 80, mock_stdscr)
        sm.load_game(loaded, 1)
        assert any(i.name == 'Persisted Gem' for i in loaded._town_items)

    def test_no_town_explored_in_old_save_does_not_crash(self, tmp_path, mock_stdscr):
        """Saves that pre-date town_explored key should load without error."""
        from classes.game import Game
        from classes.save_manager import SaveManager
        import json
        game = _make_town_game(mock_stdscr)
        sm = SaveManager(save_dir=str(tmp_path))
        sm.save_game(game, 1)
        # Strip the new key to simulate an old save file.
        save_file = tmp_path / "save_1.json"
        data = json.loads(save_file.read_text())
        data['game_state'].pop('town_explored', None)
        data['game_state'].pop('town_items', None)
        save_file.write_text(json.dumps(data))
        loaded = Game.create_minimal(24, 80, mock_stdscr)
        sm.load_game(loaded, 1)  # must not raise
        assert loaded._town_explored is None
        assert loaded._town_items == []
