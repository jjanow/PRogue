"""Tests for Game utility methods — geometry, pathfinding, item management."""
from unittest.mock import patch

import pytest

from classes.entity import Entity
from classes.item import Equipment, Item
from classes.item_loader import all_consumables


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

class TestDistance:
    def test_chebyshev_diagonal(self, minimal_game):
        a = Entity(0, 0, '@', 'A', 10, 0, 0)
        b = Entity(3, 4, 'E', 'B', 10, 0, 0)
        # Chebyshev = max(3, 4) = 4
        assert minimal_game.distance(a, b) == 4

    def test_chebyshev_horizontal(self, minimal_game):
        a = Entity(2, 5, '@', 'A', 10, 0, 0)
        b = Entity(7, 5, 'E', 'B', 10, 0, 0)
        assert minimal_game.distance(a, b) == 5

    def test_distance_zero_same_position(self, minimal_game):
        a = Entity(3, 3, '@', 'A', 10, 0, 0)
        b = Entity(3, 3, 'E', 'B', 10, 0, 0)
        assert minimal_game.distance(a, b) == 0


class TestLine:
    def test_horizontal_line_length(self, minimal_game):
        points = list(minimal_game.line(0, 0, 5, 0))
        assert len(points) == 6
        assert points[0] == (0, 0)
        assert points[-1] == (5, 0)

    def test_vertical_line(self, minimal_game):
        points = list(minimal_game.line(3, 1, 3, 4))
        assert (3, 1) in points
        assert (3, 4) in points
        assert all(x == 3 for x, y in points)

    def test_diagonal_45_degree(self, minimal_game):
        points = list(minimal_game.line(0, 0, 3, 3))
        assert (0, 0) in points
        assert (3, 3) in points

    def test_single_point_line(self, minimal_game):
        points = list(minimal_game.line(4, 4, 4, 4))
        assert points == [(4, 4)]


# ---------------------------------------------------------------------------
# FOV / line-of-sight
# ---------------------------------------------------------------------------

class TestHasLineOfSight:
    def test_same_room_clear_path(self, minimal_game):
        # Both in the room (x:2-11, y:2-6)
        assert minimal_game.has_line_of_sight(3, 3, 9, 5) is True

    def test_blocked_by_wall(self, minimal_game):
        # x=1 is a wall; target at x=0 is behind it
        assert minimal_game.has_line_of_sight(5, 4, 0, 4) is False

    def test_same_tile(self, minimal_game):
        assert minimal_game.has_line_of_sight(5, 4, 5, 4) is True

    def test_adjacent_floor_has_los(self, minimal_game):
        assert minimal_game.has_line_of_sight(5, 4, 6, 4) is True


# ---------------------------------------------------------------------------
# Room queries
# ---------------------------------------------------------------------------

class TestInRoom:
    def test_center_of_room_is_in_room(self, minimal_game):
        # Room is (2, 2, 10, 5), center approx (7, 4)
        assert minimal_game.in_room(7, 4) is True

    def test_wall_tile_not_in_room(self, minimal_game):
        assert minimal_game.in_room(0, 0) is False

    def test_corridor_tile_not_in_room(self, minimal_game):
        # There are no corridors in minimal_game, just the one room.
        # Tile (1, 4) is '#' which is not inside the room bounds.
        assert minimal_game.in_room(1, 4) is False


class TestGetRoom:
    def test_returns_room_for_floor_tile(self, minimal_game):
        room = minimal_game.get_room(5, 4)
        assert room == (2, 2, 10, 5)

    def test_returns_none_for_wall(self, minimal_game):
        assert minimal_game.get_room(0, 0) is None

    def test_returns_none_outside_all_rooms(self, minimal_game):
        assert minimal_game.get_room(15, 8) is None


# ---------------------------------------------------------------------------
# is_valid_move
# ---------------------------------------------------------------------------

class TestIsValidMove:
    def test_floor_tile_valid(self, minimal_game):
        assert minimal_game.is_valid_move(6, 4) is True

    def test_wall_tile_invalid(self, minimal_game):
        assert minimal_game.is_valid_move(0, 0) is False

    def test_negative_coords_invalid(self, minimal_game):
        assert minimal_game.is_valid_move(-1, 0) is False
        assert minimal_game.is_valid_move(0, -1) is False

    def test_out_of_bounds_coords_invalid(self, minimal_game):
        assert minimal_game.is_valid_move(100, 100) is False

    def test_stairs_tile_valid(self, minimal_game):
        # Place a '>' tile and verify it's treated as valid
        minimal_game.map[4][10] = '>'
        assert minimal_game.is_valid_move(10, 4) is True


# ---------------------------------------------------------------------------
# Pathfinding
# ---------------------------------------------------------------------------

class TestFindPath:
    def test_path_starts_at_origin_ends_at_goal(self, minimal_game):
        target = type('T', (), {'x': 9, 'y': 4})()
        path = minimal_game.find_path(minimal_game.player, target)
        assert path is not None
        assert path[0] == (minimal_game.player.x, minimal_game.player.y)
        assert path[-1] == (9, 4)

    def test_path_is_walkable(self, minimal_game):
        target = type('T', (), {'x': 8, 'y': 4})()
        path = minimal_game.find_path(minimal_game.player, target)
        assert path is not None
        for x, y in path:
            assert minimal_game.map[y][x] in ('.', '<', '>'), \
                f"Path goes through non-walkable tile at ({x},{y})"

    def test_no_path_through_solid_walls_returns_none(self, minimal_game):
        # Target is in an unreachable walled-off area
        target = type('T', (), {'x': 0, 'y': 0})()
        path = minimal_game.find_path(minimal_game.player, target)
        assert path is None

    def test_path_to_same_tile_is_single_element(self, minimal_game):
        target = type('T', (), {'x': minimal_game.player.x, 'y': minimal_game.player.y})()
        path = minimal_game.find_path(minimal_game.player, target)
        assert path is not None
        assert len(path) == 1


# ---------------------------------------------------------------------------
# pickup_item
# ---------------------------------------------------------------------------

class TestPickupItem:
    def test_pickup_adds_to_inventory(self, minimal_game):
        item = Item('Coin', lambda e: None)
        item.x, item.y = minimal_game.player.x, minimal_game.player.y
        minimal_game.items.append(item)
        minimal_game.pickup_item()
        assert any(i.name == 'Coin' for i in minimal_game.player.inventory)

    def test_pickup_removes_from_ground(self, minimal_game):
        item = Item('Gem', lambda e: None)
        item.x, item.y = minimal_game.player.x, minimal_game.player.y
        minimal_game.items.append(item)
        minimal_game.pickup_item()
        assert item not in minimal_game.items

    def test_nothing_to_pickup_appends_message(self, minimal_game):
        minimal_game.items.clear()
        minimal_game.pickup_item()
        assert any("nothing" in m.lower() for m in minimal_game.messages)

    def test_item_not_at_player_not_picked_up(self, minimal_game):
        item = Item('RemoteItem', lambda e: None)
        item.x, item.y = 0, 0  # far from player
        minimal_game.items.append(item)
        minimal_game.pickup_item()
        assert item in minimal_game.items


# ---------------------------------------------------------------------------
# drop_backpack_item
# ---------------------------------------------------------------------------

class TestDropBackpackItem:
    def test_drops_item_to_ground(self, minimal_game):
        potion = next(i for i in all_consumables if i.name == 'Health Potion')
        minimal_game.player.add_item(potion)
        minimal_game.backpack_page = 0
        minimal_game.drop_backpack_item('a')
        assert any(i.name == 'Health Potion' for i in minimal_game.items)

    def test_removes_item_from_inventory(self, minimal_game):
        # Clear inventory so only one potion exists, then drop it
        minimal_game.player.inventory.clear()
        potion = next(i for i in all_consumables if i.name == 'Health Potion')
        minimal_game.player.add_item(potion)
        minimal_game.backpack_page = 0
        minimal_game.drop_backpack_item('a')
        names = [i.name for i in minimal_game.player.inventory]
        assert 'Health Potion' not in names

    def test_dropped_item_at_player_position(self, minimal_game):
        potion = next(i for i in all_consumables if i.name == 'Health Potion')
        minimal_game.player.add_item(potion)
        minimal_game.backpack_page = 0
        minimal_game.drop_backpack_item('a')
        dropped = next((i for i in minimal_game.items if i.name == 'Health Potion'), None)
        assert dropped is not None
        assert dropped.x == minimal_game.player.x
        assert dropped.y == minimal_game.player.y

    def test_invalid_key_appends_message(self, minimal_game):
        minimal_game.player.inventory.clear()
        minimal_game.drop_backpack_item('z')
        assert any('invalid' in m.lower() for m in minimal_game.messages)


# ---------------------------------------------------------------------------
# use_backpack_item (consumable)
# ---------------------------------------------------------------------------

class TestUseBackpackItem:
    def test_consumable_effect_applied(self, minimal_game):
        minimal_game.player.inventory.clear()
        potion = next(i for i in all_consumables if i.name == 'Health Potion')
        minimal_game.player.health = 50.0
        minimal_game.player.max_health = 100.0
        minimal_game.player.add_item(potion)
        minimal_game.backpack_page = 0
        minimal_game.use_backpack_item('a')
        assert minimal_game.player.health > 50.0

    def test_consumable_removed_after_use(self, minimal_game):
        # Clear so exactly one potion exists
        minimal_game.player.inventory.clear()
        potion = next(i for i in all_consumables if i.name == 'Health Potion')
        minimal_game.player.add_item(potion)
        minimal_game.backpack_page = 0
        minimal_game.use_backpack_item('a')
        names = [i.name for i in minimal_game.player.inventory]
        assert 'Health Potion' not in names

    def test_equipment_item_gets_equipped(self, minimal_game):
        # Clear inventory so weapon is the only item at index 'a'
        minimal_game.player.inventory.clear()
        minimal_game.player.equipment['a']['item'] = None
        weapon = Equipment('Test Blade', 'weapon', 'hands', 5, damage={'min': 1, 'max': 4})
        minimal_game.player.add_item(weapon)
        minimal_game.backpack_page = 0
        minimal_game.use_backpack_item('a')
        assert minimal_game.player.equipment['a']['item'] is not None


# ---------------------------------------------------------------------------
# player_move_or_attack
# ---------------------------------------------------------------------------

class TestPlayerMoveOrAttack:
    def test_moves_to_empty_floor_tile(self, minimal_game):
        old_x, old_y = minimal_game.player.x, minimal_game.player.y
        minimal_game.player_move_or_attack(1, 0)
        assert minimal_game.player.x == old_x + 1
        assert minimal_game.player.y == old_y

    def test_does_not_move_into_wall(self, minimal_game):
        # Player at (5,4); moving (-4,0) would land in wall at x=1
        old_x, old_y = minimal_game.player.x, minimal_game.player.y
        minimal_game.player_move_or_attack(-4, 0)
        # Should not move since (1,4) is a wall
        assert minimal_game.player.x == old_x
        assert minimal_game.player.y == old_y

    def test_attacks_adjacent_enemy(self, minimal_game):
        enemy = Entity(6, 4, 'E', 'Goblin', 10, 0, 0)
        minimal_game.enemies.append(enemy)
        with patch('random.random', return_value=0.0):
            with patch('random.randint', return_value=2):
                minimal_game.player_move_or_attack(1, 0)
        assert any('Goblin' in m for m in minimal_game.messages)


# ---------------------------------------------------------------------------
# Level transitions
# ---------------------------------------------------------------------------

class TestNextLevel:
    def test_dungeon_level_increments(self, minimal_game):
        initial = minimal_game.dungeon_level
        minimal_game.next_level()
        assert minimal_game.dungeon_level == initial + 1

    def test_next_level_appends_message(self, minimal_game):
        minimal_game.next_level()
        assert any('descend' in m.lower() for m in minimal_game.messages)

    def test_next_level_generates_new_map(self, minimal_game):
        old_rooms = list(minimal_game.rooms)
        minimal_game.next_level()
        # May or may not match old rooms, but map was regenerated
        assert minimal_game.map is not None
        assert len(minimal_game.map) > 0


class TestPreviousLevel:
    def test_dungeon_level_decrements(self, minimal_game):
        minimal_game.dungeon_level = 3
        minimal_game.previous_level()
        assert minimal_game.dungeon_level == 2

    def test_previous_level_appends_message(self, minimal_game):
        minimal_game.dungeon_level = 2
        minimal_game.previous_level()
        assert any('ascend' in m.lower() for m in minimal_game.messages)


# ---------------------------------------------------------------------------
# Handle player death
# ---------------------------------------------------------------------------

class TestHandlePlayerDeath:
    def test_sets_game_over_flag(self, minimal_game):
        minimal_game.handle_player_death()
        assert minimal_game.game_over is True

    def test_sets_quit_flag(self, minimal_game):
        minimal_game.handle_player_death()
        assert minimal_game.quit is True

    def test_health_clamped_to_zero(self, minimal_game):
        minimal_game.player.health = -10.0
        minimal_game.handle_player_death()
        assert minimal_game.player.health == 0.0


# ---------------------------------------------------------------------------
# check_collisions (auto-pickup)
# ---------------------------------------------------------------------------

class TestCheckCollisions:
    def test_auto_picks_up_item_at_player_position(self, minimal_game):
        item = Item('Floor Item', lambda e: None)
        item.x, item.y = minimal_game.player.x, minimal_game.player.y
        minimal_game.items.append(item)
        minimal_game.check_collisions()
        assert any(i.name == 'Floor Item' for i in minimal_game.player.inventory)
        assert item not in minimal_game.items

    def test_leaves_items_at_other_positions(self, minimal_game):
        item = Item('Distant Item', lambda e: None)
        item.x, item.y = 0, 0
        minimal_game.items.append(item)
        minimal_game.check_collisions()
        assert item in minimal_game.items
