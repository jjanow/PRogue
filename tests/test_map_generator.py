"""Tests for MapGenerator — BSP layout, hard constraints, content types, connectivity."""
from __future__ import annotations

import random
from collections import deque

from classes.entity import Entity
from classes.map_generator import MapGenerator, RoomType, SpecialFeature

# Run each structural test across several seeds to avoid single-run fragility.
SEEDS = [0, 1, 42, 99, 1337]

_SCREEN_H = 40
_SCREEN_W = 100


def _make_gen(seed: int) -> MapGenerator:
    random.seed(seed)
    return MapGenerator(_SCREEN_H, _SCREEN_W)


def _generate(seed: int) -> tuple[MapGenerator, list[list[str]], list[tuple[int, int, int, int]]]:
    gen = _make_gen(seed)
    m, rooms = gen.generate()
    return gen, m, rooms


def _generate_level(
    seed: int,
) -> tuple[MapGenerator, list[list[str]], list[tuple[int, int, int, int]], int, int, int, int]:
    random.seed(seed)
    gen = MapGenerator(_SCREEN_H, _SCREEN_W)
    player = Entity(0, 0, '@', 'P', 100, 0, 0)
    m, rooms, ux, uy, dx, dy = gen.generate_level(player, dungeon_level=1)
    return gen, m, rooms, ux, uy, dx, dy


def _floor_tiles(m: list[list[str]]) -> set[tuple[int, int]]:
    traversable = {'.', '+', '<', '>', '^', 'A', '~', 'f', 'b', '/'}
    return {(x, y) for y, row in enumerate(m) for x, cell in enumerate(row) if cell in traversable}


def _reachable(m: list[list[str]], sx: int, sy: int) -> set[tuple[int, int]]:
    walkable = {'.', '+', '<', '>', '^', 'A', '~', 'f', 'b', '/'}
    visited: set[tuple[int, int]] = set()
    h, w = len(m), len(m[0]) if m else 0
    if not (0 <= sx < w and 0 <= sy < h) or m[sy][sx] not in walkable:
        return visited
    q: deque[tuple[int, int]] = deque([(sx, sy)])
    visited.add((sx, sy))
    while q:
        x, y = q.popleft()
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited and m[ny][nx] in walkable:
                visited.add((nx, ny))
                q.append((nx, ny))
    return visited


# ---------------------------------------------------------------------------
# Map dimensions
# ---------------------------------------------------------------------------

class TestMapDimensions:
    def test_map_always_80_wide(self) -> None:
        for seed in SEEDS:
            _, m, _ = _generate(seed)
            for row in m:
                assert len(row) == 80, f"Seed {seed}: row width {len(row)} != 80"

    def test_map_always_23_tall(self) -> None:
        for seed in SEEDS:
            _, m, _ = _generate(seed)
            assert len(m) == 23, f"Seed {seed}: map height {len(m)} != 23"

    def test_generator_height_width_attributes(self) -> None:
        gen = MapGenerator(30, 50)
        assert gen.height == 23
        assert gen.width == 80


# ---------------------------------------------------------------------------
# Room count
# ---------------------------------------------------------------------------

class TestRoomCount:
    def test_at_least_8_rooms(self) -> None:
        for seed in SEEDS:
            _, _, rooms = _generate(seed)
            assert len(rooms) >= 8, f"Seed {seed}: only {len(rooms)} rooms"

    def test_room_count_upper_bound(self) -> None:
        for seed in SEEDS:
            _, _, rooms = _generate(seed)
            assert len(rooms) <= 25, f"Seed {seed}: suspiciously many rooms ({len(rooms)})"


# ---------------------------------------------------------------------------
# Tile-budget constraints
# ---------------------------------------------------------------------------

class TestTileBudget:
    def _counts(
        self, m: list[list[str]], rooms: list[tuple[int, int, int, int]]
    ) -> tuple[int, int]:
        floor = sum(1 for row in m for c in row if c == '.')
        room_floor = sum(rw * rh for _, _, rw, rh in rooms)
        return floor, room_floor

    def test_room_coverage_at_least_40_percent(self) -> None:
        for seed in SEEDS:
            gen, m, rooms = _generate(seed)
            traversable = sum(
                1 for row in m
                for c in row
                if c in ('.', '+', '<', '>', '^', 'A', '~', 'f', 'b', '/')
            )
            # room floor approximation from rects (no overlap in BSP)
            room_floor = sum(rw * rh for _, _, rw, rh in rooms)
            if traversable > 0:
                assert room_floor / traversable >= 0.40, (
                    f"Seed {seed}: room coverage {room_floor/traversable:.2%} < 40%"
                )

    def test_corridor_ratio_at_most_45_percent(self) -> None:
        for seed in SEEDS:
            _, m, rooms = _generate(seed)
            floor = sum(1 for row in m for c in row if c == '.')
            room_floor = sum(rw * rh for _, _, rw, rh in rooms)
            if floor > 0:
                corridor = floor - room_floor
                assert corridor / floor <= 0.45, (
                    f"Seed {seed}: corridor ratio {corridor/floor:.2%} > 45%"
                )


# ---------------------------------------------------------------------------
# Room geometry
# ---------------------------------------------------------------------------

class TestRoomGeometry:
    def test_rooms_within_map_bounds(self) -> None:
        for seed in SEEDS:
            _, _, rooms = _generate(seed)
            for rx, ry, rw, rh in rooms:
                assert 0 <= rx and rx + rw <= 80, f"Seed {seed}: room x out of bounds"
                assert 0 <= ry and ry + rh <= 23, f"Seed {seed}: room y out of bounds"

    def test_rooms_are_floor(self) -> None:
        for seed in SEEDS:
            _, m, rooms = _generate(seed)
            for rx, ry, rw, rh in rooms:
                cx, cy = rx + rw // 2, ry + rh // 2
                assert m[cy][cx] in ('.', '<', '>'), (
                    f"Seed {seed}: room centre ({cx},{cy}) not floor"
                )

    def test_rooms_min_size_3x3(self) -> None:
        for seed in SEEDS:
            _, _, rooms = _generate(seed)
            for rx, ry, rw, rh in rooms:
                assert rw >= 3 and rh >= 3, (
                    f"Seed {seed}: room ({rw}×{rh}) smaller than 3×3"
                )

    def test_rooms_max_size_9x6(self) -> None:
        for seed in SEEDS:
            _, _, rooms = _generate(seed)
            for rx, ry, rw, rh in rooms:
                assert rw <= 9 and rh <= 6, (
                    f"Seed {seed}: room ({rw}×{rh}) exceeds 9×6 max"
                )


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------

class TestConnectivity:
    def test_all_rooms_reachable_from_stairs(self) -> None:
        for seed in SEEDS:
            gen, m, rooms, ux, uy, dx, dy = _generate_level(seed)
            reached = _reachable(m, ux, uy)
            for idx, (rx, ry, rw, rh) in enumerate(rooms):
                cx, cy = rx + rw // 2, ry + rh // 2
                assert (cx, cy) in reached, (
                    f"Seed {seed}: room {idx} centre ({cx},{cy}) unreachable"
                )

    def test_down_stairs_reachable(self) -> None:
        for seed in SEEDS:
            _, m, _, ux, uy, dx, dy = _generate_level(seed)
            reached = _reachable(m, ux, uy)
            assert (dx, dy) in reached, f"Seed {seed}: down-stairs unreachable"


# ---------------------------------------------------------------------------
# Stair placement
# ---------------------------------------------------------------------------

class TestStairPlacement:
    def test_up_stair_tile(self) -> None:
        for seed in SEEDS:
            _, m, _, ux, uy, _, _ = _generate_level(seed)
            assert m[uy][ux] == '<', f"Seed {seed}: up-stairs not '<'"

    def test_down_stair_tile(self) -> None:
        for seed in SEEDS:
            _, m, _, _, _, dx, dy = _generate_level(seed)
            assert m[dy][dx] == '>', f"Seed {seed}: down-stairs not '>'"

    def test_stairs_in_different_positions(self) -> None:
        for seed in SEEDS:
            _, _, _, ux, uy, dx, dy = _generate_level(seed)
            assert (ux, uy) != (dx, dy), f"Seed {seed}: stairs at same position"

    def test_player_at_up_stairs(self) -> None:
        for seed in SEEDS:
            random.seed(seed)
            gen = MapGenerator(_SCREEN_H, _SCREEN_W)
            player = Entity(0, 0, '@', 'P', 100, 0, 0)
            _, _, ux, uy, _, _ = gen.generate_level(player, dungeon_level=1)
            assert player.x == ux and player.y == uy, f"Seed {seed}: player not at up-stairs"


# ---------------------------------------------------------------------------
# Content types
# ---------------------------------------------------------------------------

class TestContentTypes:
    def test_every_room_has_a_type(self) -> None:
        for seed in SEEDS:
            gen, _, rooms, *_ = _generate_level(seed)
            for idx in range(len(rooms)):
                assert idx in gen.room_types, f"Seed {seed}: room {idx} has no type"

    def test_all_types_are_valid(self) -> None:
        valid = set(RoomType)
        for seed in SEEDS:
            gen, _, rooms, *_ = _generate_level(seed)
            for idx, t in gen.room_types.items():
                assert t in valid, f"Seed {seed}: unknown room type {t!r}"

    def test_at_most_one_shop(self) -> None:
        for seed in SEEDS:
            gen, _, _, *_ = _generate_level(seed)
            shops = sum(1 for t in gen.room_types.values() if t == RoomType.SHOP)
            assert shops <= 1, f"Seed {seed}: {shops} shops found (max 1)"

    def test_has_at_least_one_monster_den(self) -> None:
        for seed in SEEDS:
            gen, _, _, *_ = _generate_level(seed)
            dens = sum(1 for t in gen.room_types.values() if t == RoomType.MONSTER_DEN)
            assert dens >= 1, f"Seed {seed}: no monster den"

    def test_special_features_assigned_to_special_rooms(self) -> None:
        for seed in SEEDS:
            gen, _, _, *_ = _generate_level(seed)
            for idx, feat in gen.special_features.items():
                assert gen.room_types[idx] == RoomType.SPECIAL, (
                    f"Seed {seed}: feature on non-SPECIAL room {idx}"
                )
                assert feat in set(SpecialFeature)

    def test_tension_flag_matches_room_types(self) -> None:
        for seed in SEEDS:
            gen, _, _, *_ = _generate_level(seed)
            has_tension = any(t == RoomType.TENSION for t in gen.room_types.values())
            assert gen.has_tension_room == has_tension


# ---------------------------------------------------------------------------
# Door placement
# ---------------------------------------------------------------------------

class TestDoorPlacement:
    def test_map_contains_some_doors(self) -> None:
        for seed in SEEDS:
            _, m, _, *_ = _generate_level(seed)
            door_count = sum(1 for row in m for c in row if c == '+')
            assert door_count > 0, f"Seed {seed}: no doors placed"


# ---------------------------------------------------------------------------
# Valid tile chars
# ---------------------------------------------------------------------------

class TestValidTiles:
    def test_only_valid_tiles(self) -> None:
        valid = {'.', '#', '<', '>', '+', '/', '^', 'A', '~', 'f', 'b', 'T', ' '}
        for seed in SEEDS:
            _, m, _, *_ = _generate_level(seed)
            for y, row in enumerate(m):
                for x, c in enumerate(row):
                    assert c in valid, (
                        f"Seed {seed}: unexpected tile '{c}' at ({x},{y})"
                    )


# ---------------------------------------------------------------------------
# Fallback template
# ---------------------------------------------------------------------------

class TestFallback:
    def test_fallback_produces_valid_map(self) -> None:
        gen = MapGenerator(_SCREEN_H, _SCREEN_W)
        grid, rooms = gen._minimal_fallback()
        assert len(grid) == 23
        assert all(len(row) == 80 for row in grid)
        assert len(rooms) == 8  # 4 cols × 2 rows

    def test_fallback_rooms_are_connected(self) -> None:
        gen = MapGenerator(_SCREEN_H, _SCREEN_W)
        grid, rooms = gen._minimal_fallback()
        r0 = rooms[0]
        sx, sy = r0[0] + r0[2] // 2, r0[1] + r0[3] // 2
        reached = _reachable(grid, sx, sy)
        for idx, (rx, ry, rw, rh) in enumerate(rooms):
            cx, cy = rx + rw // 2, ry + rh // 2
            assert (cx, cy) in reached, f"Fallback room {idx} unreachable"
