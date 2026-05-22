"""Tests for MapGenerator — size clamping, room layout invariants, connectivity."""
import random
from collections import deque

import pytest

from classes.map_generator import MapGenerator


# Generate several maps with different seeds to avoid fragile single-run assertions.
SEEDS = [0, 1, 42, 99, 1337]


def generate_with_seed(seed, h=20, w=40, sh=30, sw=50):
    random.seed(seed)
    gen = MapGenerator(h, w, sh, sw)
    map_data, rooms = gen.generate()
    return gen, map_data, rooms


# ---------------------------------------------------------------------------
# Size clamping
# ---------------------------------------------------------------------------

class TestSizeClamping:
    def test_height_clamps_to_minimum_10(self):
        gen = MapGenerator(5, 40, 30, 60)
        assert gen.height >= 10

    def test_width_clamps_to_minimum_20(self):
        gen = MapGenerator(20, 10, 30, 30)
        assert gen.width >= 20

    def test_height_clamped_by_screen_height(self):
        gen = MapGenerator(100, 40, 20, 60)
        # Must be at most screen_height - 6
        assert gen.height <= 20 - 6

    def test_width_clamped_by_screen_width(self):
        gen = MapGenerator(20, 100, 30, 40)
        # Must be at most screen_width - 5
        assert gen.width <= 40 - 5

    def test_sensible_medium_dimensions_preserved(self):
        gen = MapGenerator(20, 40, 30, 50)
        assert gen.height == 20
        assert gen.width == 40


# ---------------------------------------------------------------------------
# Map output
# ---------------------------------------------------------------------------

class TestMapOutput:
    def test_map_has_correct_dimensions(self):
        for seed in SEEDS:
            gen, map_data, _ = generate_with_seed(seed)
            assert len(map_data) == gen.height, f"Seed {seed}: wrong row count"
            for row in map_data:
                assert len(row) == gen.width, f"Seed {seed}: wrong col count"

    def test_bottom_row_all_walls(self):
        for seed in SEEDS:
            gen, map_data, _ = generate_with_seed(seed)
            assert all(c == '#' for c in map_data[-1]), f"Seed {seed}: bottom row has non-wall"

    def test_map_contains_only_valid_tiles(self):
        valid = {'.', '#', '<', '>'}
        for seed in SEEDS:
            _, map_data, _ = generate_with_seed(seed)
            for y, row in enumerate(map_data):
                for x, c in enumerate(row):
                    assert c in valid, f"Invalid tile '{c}' at ({x},{y})"


# ---------------------------------------------------------------------------
# Room layout
# ---------------------------------------------------------------------------

class TestRoomLayout:
    def test_rooms_within_map_bounds(self):
        for seed in SEEDS:
            gen, _, rooms = generate_with_seed(seed)
            for rx, ry, rw, rh in rooms:
                assert rx >= 0 and rx + rw <= gen.width, f"Room x out of bounds"
                assert ry >= 0 and ry + rh <= gen.height, f"Room y out of bounds"

    def test_room_floor_tiles_exist_in_map(self):
        for seed in SEEDS:
            gen, map_data, rooms = generate_with_seed(seed)
            for rx, ry, rw, rh in rooms:
                cx = rx + rw // 2
                cy = ry + rh // 2
                assert map_data[cy][cx] in ('.', '<', '>'), \
                    f"Seed {seed}: room center ({cx},{cy}) is not floor"

    def test_rooms_not_directly_adjacent(self):
        """Rooms must have at least 1 wall tile between them in every dimension."""
        for seed in SEEDS:
            _, _, rooms = generate_with_seed(seed)
            for i in range(len(rooms)):
                for j in range(i + 1, len(rooms)):
                    rx1, ry1, rw1, rh1 = rooms[i]
                    rx2, ry2, rw2, rh2 = rooms[j]
                    separated = (
                        rx1 + rw1 < rx2 or rx2 + rw2 < rx1 or
                        ry1 + rh1 < ry2 or ry2 + rh2 < ry1
                    )
                    assert separated, \
                        f"Seed {seed}: rooms {i} and {j} overlap or are adjacent"


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------

class TestConnectivity:
    def _reachable_from(self, map_data, start_x, start_y, height, width):
        visited = {(start_x, start_y)}
        queue = deque([(start_x, start_y)])
        dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
        while queue:
            x, y = queue.popleft()
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and
                        map_data[ny][nx] in ('.', '<', '>') and
                        (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        return visited

    def test_all_room_centers_reachable_from_first(self):
        for seed in SEEDS:
            gen, map_data, rooms = generate_with_seed(seed)
            if len(rooms) < 2:
                continue
            rx, ry, rw, rh = rooms[0]
            start_x = rx + rw // 2
            start_y = ry + rh // 2
            reachable = self._reachable_from(map_data, start_x, start_y,
                                             gen.height, gen.width)
            for idx, (rx2, ry2, rw2, rh2) in enumerate(rooms[1:], 1):
                cx, cy = rx2 + rw2 // 2, ry2 + rh2 // 2
                assert (cx, cy) in reachable, \
                    f"Seed {seed}: room {idx} center ({cx},{cy}) unreachable"


# ---------------------------------------------------------------------------
# generate_level
# ---------------------------------------------------------------------------

class TestGenerateLevel:
    def test_places_stairs_on_floor_tiles(self):
        for seed in SEEDS:
            random.seed(seed)
            gen = MapGenerator(20, 40, 30, 50)
            from classes.entity import Entity
            player = Entity(0, 0, '@', 'P', 100, 0, 0)
            map_data, rooms, ux, uy, dx, dy = gen.generate_level(player)
            assert map_data[uy][ux] == '<', f"Seed {seed}: stairs-up not '<'"
            assert map_data[dy][dx] == '>', f"Seed {seed}: stairs-down not '>'"

    def test_player_placed_at_stairs_up(self):
        random.seed(42)
        gen = MapGenerator(20, 40, 30, 50)
        from classes.entity import Entity
        player = Entity(0, 0, '@', 'P', 100, 0, 0)
        _, rooms, ux, uy, dx, dy = gen.generate_level(player)
        assert player.x == ux
        assert player.y == uy
