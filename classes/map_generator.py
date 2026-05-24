from __future__ import annotations

import random
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.entity import Entity

# Fixed map dimensions per spec
_MAP_W = 80
_MAP_H = 23

# BSP cell size constraints
_MIN_CELL_W = 10
_MIN_CELL_H = 8

# Corridor constraint: max new (non-room) floor tiles carved per corridor
_MAX_CORRIDOR_NEW_TILES = 15

# Tile-budget hard constraints
_MAX_CORRIDOR_RATIO = 0.45   # corridor_tiles / all_traversable
_MIN_ROOM_COVERAGE = 0.40    # room_floor_tiles / all_traversable

_MAX_ATTEMPTS = 10
_DOOR_RATE = 0.70


class RoomType(str, Enum):
    EMPTY = "empty"
    MONSTER_DEN = "monster_den"
    TREASURE = "treasure"
    SPECIAL = "special"
    TENSION = "tension"
    SHOP = "shop"


class SpecialFeature(str, Enum):
    ALTAR = "altar"
    FOUNTAIN = "fountain"
    FORGE = "forge"
    HERB_CLUSTER = "herb_cluster"
    TRAP_CLUSTER = "trap_cluster"


_FEATURE_TILE: dict[SpecialFeature, str] = {
    SpecialFeature.ALTAR: 'A',
    SpecialFeature.FOUNTAIN: '~',
    SpecialFeature.FORGE: 'f',
    SpecialFeature.HERB_CLUSTER: 'b',
    SpecialFeature.TRAP_CLUSTER: '^',
}


@dataclass
class _BSPNode:
    x: int
    y: int
    w: int
    h: int
    left: _BSPNode | None = field(default=None, repr=False)
    right: _BSPNode | None = field(default=None, repr=False)
    room: tuple[int, int, int, int] | None = None


class MapGenerator:
    MAP_W: int = _MAP_W
    MAP_H: int = _MAP_H

    def __init__(self, screen_height: int, screen_width: int) -> None:
        self.screen_height: int = screen_height
        self.screen_width: int = screen_width
        self.height: int = _MAP_H
        self.width: int = _MAP_W
        self.map: list[list[str]] = []
        self.rooms: list[tuple[int, int, int, int]] = []
        # Populated by generate_level(); game.py reads these for content spawning
        self.room_types: dict[int, RoomType] = {}
        self.special_features: dict[int, SpecialFeature] = {}
        self.has_tension_room: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> tuple[list[list[str]], list[tuple[int, int, int, int]]]:
        """Return map grid and room list without stairs or content metadata."""
        for _ in range(_MAX_ATTEMPTS):
            result = self._attempt_map()
            if result is not None:
                self.map, self.rooms = result
                return self.map, self.rooms
        self.map, self.rooms = self._minimal_fallback()
        return self.map, self.rooms

    def generate_level(
        self,
        player: Entity,
        dungeon_level: int = 1,
    ) -> tuple[list[list[str]], list[tuple[int, int, int, int]], int, int, int, int]:
        """Full level: map + stairs + content types + features. Sets player start."""
        for _ in range(_MAX_ATTEMPTS):
            result = self._attempt_level(player, dungeon_level)
            if result is not None:
                return result
        return self._fallback_level(player)

    # ------------------------------------------------------------------
    # Core generation attempt
    # ------------------------------------------------------------------

    def _attempt_map(
        self,
    ) -> tuple[list[list[str]], list[tuple[int, int, int, int]]] | None:
        grid: list[list[str]] = [['#'] * _MAP_W for _ in range(_MAP_H)]
        room_floor: list[list[bool]] = [[False] * _MAP_W for _ in range(_MAP_H)]

        root = _BSPNode(0, 0, _MAP_W, _MAP_H)
        self._partition(root)

        rooms: list[tuple[int, int, int, int]] = []
        self._place_rooms(root, grid, room_floor, rooms)

        if len(rooms) < 8:
            return None

        if self._connect_bsp(root, grid):
            return None  # A corridor exceeded the length limit

        # Tile-budget validation
        floor_count = sum(
            1 for y in range(_MAP_H) for x in range(_MAP_W) if grid[y][x] == '.'
        )
        room_count = sum(
            1 for y in range(_MAP_H) for x in range(_MAP_W) if room_floor[y][x]
        )
        if floor_count == 0:
            return None
        corridor_count = floor_count - room_count
        if corridor_count / floor_count > _MAX_CORRIDOR_RATIO:
            return None
        if room_count / floor_count < _MIN_ROOM_COVERAGE:
            return None

        return grid, rooms

    def _attempt_level(
        self,
        player: Entity,
        dungeon_level: int,
    ) -> tuple[list[list[str]], list[tuple[int, int, int, int]], int, int, int, int] | None:
        pair = self._attempt_map()
        if pair is None:
            return None
        grid, rooms = pair

        # Solid outer border
        for x in range(_MAP_W):
            grid[0][x] = '#'
            grid[_MAP_H - 1][x] = '#'
        for y in range(_MAP_H):
            grid[y][0] = '#'
            grid[y][_MAP_W - 1] = '#'

        # Assign content types (needed before selecting stair rooms)
        self._assign_content_types(rooms, dungeon_level)

        # Seal tension rooms to a single corridor entry; connectivity check follows
        self._seal_tension_rooms(grid, rooms)

        # Stair rooms: avoid TENSION / SHOP
        eligible = [
            i for i in range(len(rooms))
            if self.room_types.get(i) not in (RoomType.TENSION, RoomType.SHOP)
        ]
        if len(eligible) < 2:
            eligible = list(range(len(rooms)))

        up_idx = random.choice(eligible)
        rest = [i for i in eligible if i != up_idx]
        if not rest:
            rest = [0 if up_idx != 0 else len(rooms) - 1]

        up_cx = rooms[up_idx][0] + rooms[up_idx][2] // 2
        up_cy = rooms[up_idx][1] + rooms[up_idx][3] // 2
        down_idx = max(
            rest,
            key=lambda i: (
                abs(rooms[i][0] + rooms[i][2] // 2 - up_cx)
                + abs(rooms[i][1] + rooms[i][3] // 2 - up_cy)
            ),
        )

        up_x = rooms[up_idx][0] + rooms[up_idx][2] // 2
        up_y = rooms[up_idx][1] + rooms[up_idx][3] // 2
        dn_x = rooms[down_idx][0] + rooms[down_idx][2] // 2
        dn_y = rooms[down_idx][1] + rooms[down_idx][3] // 2
        grid[up_y][up_x] = '<'
        grid[dn_y][dn_x] = '>'

        # Flood-fill connectivity check from up-stairs
        reachable = self._flood_fill(grid, up_x, up_y)
        for rx, ry, rw, rh in rooms:
            if (rx + rw // 2, ry + rh // 2) not in reachable:
                return None

        self._place_doors(grid, rooms)
        self._place_special_features(grid, rooms)
        self._place_ambient_traps(grid, rooms)

        player.x, player.y = up_x, up_y
        self.map = grid
        self.rooms = rooms
        return grid, rooms, up_x, up_y, dn_x, dn_y

    # ------------------------------------------------------------------
    # BSP partitioning
    # ------------------------------------------------------------------

    def _partition(self, node: _BSPNode) -> None:
        can_h = node.h >= 2 * _MIN_CELL_H  # top/bottom split
        can_v = node.w >= 2 * _MIN_CELL_W  # left/right split
        if not can_h and not can_v:
            return
        split_h = (node.h >= node.w) if (can_h and can_v) else can_h

        if split_h:
            lo, hi = _MIN_CELL_H, node.h - _MIN_CELL_H
            if lo > hi:
                return
            s = random.randint(lo, hi)
            node.left = _BSPNode(node.x, node.y, node.w, s)
            node.right = _BSPNode(node.x, node.y + s, node.w, node.h - s)
        else:
            lo, hi = _MIN_CELL_W, node.w - _MIN_CELL_W
            if lo > hi:
                return
            s = random.randint(lo, hi)
            node.left = _BSPNode(node.x, node.y, s, node.h)
            node.right = _BSPNode(node.x + s, node.y, node.w - s, node.h)

        self._partition(node.left)
        self._partition(node.right)

    # ------------------------------------------------------------------
    # Room placement
    # ------------------------------------------------------------------

    def _place_rooms(
        self,
        node: _BSPNode,
        grid: list[list[str]],
        room_floor: list[list[bool]],
        rooms: list[tuple[int, int, int, int]],
    ) -> None:
        if node.left is None and node.right is None:
            room = self._place_one_room(node, grid, room_floor)
            if room:
                node.room = room
                rooms.append(room)
            return
        if node.left:
            self._place_rooms(node.left, grid, room_floor, rooms)
        if node.right:
            self._place_rooms(node.right, grid, room_floor, rooms)

    def _place_one_room(
        self,
        node: _BSPNode,
        grid: list[list[str]],
        room_floor: list[list[bool]],
    ) -> tuple[int, int, int, int] | None:
        margin = 2
        max_rw = min(9, node.w - 2 * margin)
        max_rh = min(6, node.h - 2 * margin)
        if max_rw < 3 or max_rh < 3:
            # Cell too tight: squeeze in minimal room with 1-tile margin
            margin = 1
            max_rw = max(3, node.w - 2 * margin)
            max_rh = max(3, node.h - 2 * margin)
            if max_rw < 3 or max_rh < 3:
                return None

        rw = random.randint(3, max_rw)
        rh = random.randint(3, max_rh)

        x_lo = node.x + margin
        x_hi = node.x + node.w - margin - rw
        y_lo = node.y + margin
        y_hi = node.y + node.h - margin - rh
        if x_lo > x_hi:
            x_lo = x_hi = node.x + max(0, (node.w - rw) // 2)
        if y_lo > y_hi:
            y_lo = y_hi = node.y + max(0, (node.h - rh) // 2)

        rx = random.randint(x_lo, x_hi)
        ry = random.randint(y_lo, y_hi)
        rx = max(1, min(rx, _MAP_W - 1 - rw))
        ry = max(1, min(ry, _MAP_H - 1 - rh))

        for row in range(ry, ry + rh):
            for col in range(rx, rx + rw):
                if 0 <= row < _MAP_H and 0 <= col < _MAP_W:
                    grid[row][col] = '.'
                    room_floor[row][col] = True
        return rx, ry, rw, rh

    # ------------------------------------------------------------------
    # BSP corridor connection
    # ------------------------------------------------------------------

    def _connect_bsp(self, node: _BSPNode, grid: list[list[str]]) -> bool:
        """Recursively connect BSP siblings with L-shaped corridors.

        Returns True if any single corridor exceeded _MAX_CORRIDOR_NEW_TILES,
        which causes the entire attempt to be discarded."""
        if node.left is None or node.right is None:
            return False

        exceeded = self._connect_bsp(node.left, grid) or self._connect_bsp(node.right, grid)

        left_rooms = self._leaf_rooms(node.left)
        right_rooms = self._leaf_rooms(node.right)
        if not left_rooms or not right_rooms:
            return exceeded

        # Nearest room pair by boundary-to-boundary distance
        best_d = float('inf')
        best_r1 = left_rooms[0]
        best_r2 = right_rooms[0]
        for r1 in left_rooms:
            for r2 in right_rooms:
                d = _bdist(r1, r2)
                if d < best_d:
                    best_d, best_r1, best_r2 = d, r1, r2

        # Boundary points on each room facing the other room's center
        cx1 = best_r1[0] + best_r1[2] // 2
        cy1 = best_r1[1] + best_r1[3] // 2
        cx2 = best_r2[0] + best_r2[2] // 2
        cy2 = best_r2[1] + best_r2[3] // 2
        p1 = _bpoint(best_r1, cx2, cy2)
        p2 = _bpoint(best_r2, cx1, cy1)

        # Pick whichever L-orientation carves fewer new tiles
        tiles_hv = self._l_tiles(p1[0], p1[1], p2[0], p2[1], True)
        tiles_vh = self._l_tiles(p1[0], p1[1], p2[0], p2[1], False)
        new_hv = sum(
            1 for x, y in tiles_hv
            if 0 <= y < _MAP_H and 0 <= x < _MAP_W and grid[y][x] == '#'
        )
        new_vh = sum(
            1 for x, y in tiles_vh
            if 0 <= y < _MAP_H and 0 <= x < _MAP_W and grid[y][x] == '#'
        )
        tiles = tiles_hv if new_hv <= new_vh else tiles_vh
        new_count = min(new_hv, new_vh)

        for x, y in tiles:
            if 0 <= y < _MAP_H and 0 <= x < _MAP_W:
                grid[y][x] = '.'

        return exceeded or new_count > _MAX_CORRIDOR_NEW_TILES

    def _leaf_rooms(
        self, node: _BSPNode | None
    ) -> list[tuple[int, int, int, int]]:
        if node is None:
            return []
        if node.left is None and node.right is None:
            return [node.room] if node.room else []
        return self._leaf_rooms(node.left) + self._leaf_rooms(node.right)

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def _l_tiles(
        self, x1: int, y1: int, x2: int, y2: int, h_first: bool
    ) -> list[tuple[int, int]]:
        tx, ty = (x2, y1) if h_first else (x1, y2)
        seg1 = list(_straight(x1, y1, tx, ty))
        seg2 = list(_straight(tx, ty, x2, y2))
        return seg1 + seg2[1:]

    # ------------------------------------------------------------------
    # Tension room sealing (single entry point)
    # ------------------------------------------------------------------

    def _seal_tension_rooms(
        self,
        grid: list[list[str]],
        rooms: list[tuple[int, int, int, int]],
    ) -> None:
        for idx, rtype in self.room_types.items():
            if rtype != RoomType.TENSION:
                continue
            rx, ry, rw, rh = rooms[idx]
            exterior: list[tuple[int, int]] = []
            for dx in range(rw):
                exterior.append((rx + dx, ry - 1))
                exterior.append((rx + dx, ry + rh))
            for dy in range(rh):
                exterior.append((rx - 1, ry + dy))
                exterior.append((rx + rw, ry + dy))

            entries = [
                (x, y) for (x, y) in exterior
                if 0 <= y < _MAP_H and 0 <= x < _MAP_W
                and grid[y][x] == '.'
                and not _in_room(x, y, rooms)
            ]
            if not entries:
                continue
            door_x, door_y = random.choice(entries)
            grid[door_y][door_x] = '+'
            for x, y in entries:
                if (x, y) != (door_x, door_y):
                    grid[y][x] = '#'

    # ------------------------------------------------------------------
    # Door placement
    # ------------------------------------------------------------------

    def _place_doors(
        self,
        grid: list[list[str]],
        rooms: list[tuple[int, int, int, int]],
    ) -> None:
        for y in range(1, _MAP_H - 1):
            for x in range(1, _MAP_W - 1):
                if grid[y][x] != '.':
                    continue
                if _in_room(x, y, rooms):
                    continue
                if (
                    any(
                        _in_room(x + dx, y + dy, rooms)
                        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    )
                    and random.random() < _DOOR_RATE
                ):
                    grid[y][x] = '+'

    # ------------------------------------------------------------------
    # Content type assignment
    # ------------------------------------------------------------------

    def _assign_content_types(
        self,
        rooms: list[tuple[int, int, int, int]],
        dungeon_level: int,
    ) -> None:
        n = len(rooms)
        targets: dict[RoomType, int] = {
            RoomType.SHOP: min(1, max(0, round(n * 0.05))),
            RoomType.TENSION: max(1, round(n * 0.10)),
            RoomType.TREASURE: max(1, round(n * 0.15)),
            RoomType.SPECIAL: max(1, round(n * 0.20)),
            RoomType.EMPTY: max(1, round(n * 0.20)),
        }
        targets[RoomType.MONSTER_DEN] = max(1, n - sum(targets.values()))

        # Normalise total to exactly n rooms
        total = sum(targets.values())
        diff = n - total
        for adjust_type in (RoomType.EMPTY, RoomType.MONSTER_DEN, RoomType.SPECIAL):
            if diff == 0:
                break
            if diff > 0:
                targets[adjust_type] += diff
                diff = 0
            elif targets[adjust_type] > 1:
                cut = min(-diff, targets[adjust_type] - 1)
                targets[adjust_type] -= cut
                diff += cut

        assignment: list[RoomType] = []
        for t, c in targets.items():
            assignment.extend([t] * c)
        # Pad or trim if rounding left a mismatch
        while len(assignment) < n:
            assignment.append(RoomType.EMPTY)
        assignment = assignment[:n]
        random.shuffle(assignment)

        # Demote SHOP to EMPTY if the room is too small (min 5×4)
        for i, (room, rtype) in enumerate(zip(rooms, assignment)):
            if rtype == RoomType.SHOP and (room[2] < 5 or room[3] < 4):
                assignment[i] = RoomType.EMPTY

        self.room_types = {i: t for i, t in enumerate(assignment)}
        self.has_tension_room = RoomType.TENSION in self.room_types.values()

        # Assign one special feature per SPECIAL room
        self.special_features = {}
        has_altar = has_forge = False
        all_features = list(SpecialFeature)
        if dungeon_level < 4:
            all_features = [
                f for f in all_features
                if f not in (SpecialFeature.ALTAR, SpecialFeature.FORGE)
            ]

        for idx, rtype in self.room_types.items():
            if rtype != RoomType.SPECIAL:
                continue
            cands = [f for f in all_features]
            if has_altar:
                cands = [f for f in cands if f != SpecialFeature.ALTAR]
            if has_forge:
                cands = [f for f in cands if f != SpecialFeature.FORGE]
            if not cands:
                cands = [
                    SpecialFeature.FOUNTAIN,
                    SpecialFeature.HERB_CLUSTER,
                    SpecialFeature.TRAP_CLUSTER,
                ]
            feat = random.choice(cands)
            self.special_features[idx] = feat
            if feat == SpecialFeature.ALTAR:
                has_altar = True
            elif feat == SpecialFeature.FORGE:
                has_forge = True

    # ------------------------------------------------------------------
    # Special feature tile placement
    # ------------------------------------------------------------------

    def _place_special_features(
        self,
        grid: list[list[str]],
        rooms: list[tuple[int, int, int, int]],
    ) -> None:
        for idx, feat in self.special_features.items():
            rx, ry, rw, rh = rooms[idx]
            tile = _FEATURE_TILE[feat]

            if feat in (SpecialFeature.HERB_CLUSTER, SpecialFeature.TRAP_CLUSTER):
                count = (
                    random.randint(2, 3)
                    if feat == SpecialFeature.TRAP_CLUSTER
                    else random.randint(2, 4)
                )
                cands = [
                    (rx + dx, ry + dy)
                    for dy in range(rh)
                    for dx in range(rw)
                    if grid[ry + dy][rx + dx] == '.'
                ]
                random.shuffle(cands)
                for cx, cy in cands[:count]:
                    grid[cy][cx] = tile
            else:
                cx, cy = rx + rw // 2, ry + rh // 2
                if grid[cy][cx] == '.':
                    grid[cy][cx] = tile

    # ------------------------------------------------------------------
    # Ambient trap placement (1 per 40 traversable tiles, on corridors)
    # ------------------------------------------------------------------

    def _place_ambient_traps(
        self,
        grid: list[list[str]],
        rooms: list[tuple[int, int, int, int]],
    ) -> None:
        total = sum(
            1 for y in range(_MAP_H) for x in range(_MAP_W)
            if grid[y][x] in ('.', '+')
        )
        count = total // 40
        corridor_tiles = [
            (x, y)
            for y in range(1, _MAP_H - 1)
            for x in range(1, _MAP_W - 1)
            if grid[y][x] == '.' and not _in_room(x, y, rooms)
        ]
        random.shuffle(corridor_tiles)
        for x, y in corridor_tiles[:count]:
            grid[y][x] = '^'

    # ------------------------------------------------------------------
    # Connectivity validation
    # ------------------------------------------------------------------

    def _flood_fill(
        self, grid: list[list[str]], sx: int, sy: int
    ) -> set[tuple[int, int]]:
        walkable = {'.', '+', '<', '>', '^', 'A', '~', 'f', 'b'}
        visited: set[tuple[int, int]] = set()
        if not (0 <= sx < _MAP_W and 0 <= sy < _MAP_H):
            return visited
        if grid[sy][sx] not in walkable:
            return visited
        q: deque[tuple[int, int]] = deque([(sx, sy)])
        visited.add((sx, sy))
        while q:
            x, y = q.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < _MAP_W
                    and 0 <= ny < _MAP_H
                    and (nx, ny) not in visited
                    and grid[ny][nx] in walkable
                ):
                    visited.add((nx, ny))
                    q.append((nx, ny))
        return visited

    # ------------------------------------------------------------------
    # Fallback: 4-column × 2-row grid (8 rooms, always valid)
    # ------------------------------------------------------------------

    def _minimal_fallback(
        self,
    ) -> tuple[list[list[str]], list[tuple[int, int, int, int]]]:
        grid: list[list[str]] = [['#'] * _MAP_W for _ in range(_MAP_H)]
        rooms: list[tuple[int, int, int, int]] = []
        cols, row_count = 4, 2
        cell_w = _MAP_W // cols  # 20
        cell_h = _MAP_H // row_count  # 11

        for row in range(row_count):
            for col in range(cols):
                rx = col * cell_w + cell_w // 2 - 2
                ry = row * cell_h + cell_h // 2 - 1
                rw, rh = 4, 3
                rx = max(1, min(rx, _MAP_W - rw - 1))
                ry = max(1, min(ry, _MAP_H - rh - 1))
                for y in range(ry, ry + rh):
                    for x in range(rx, rx + rw):
                        grid[y][x] = '.'
                rooms.append((rx, ry, rw, rh))

        # Horizontal corridors within each row
        for row in range(row_count):
            for col in range(cols - 1):
                r1 = rooms[row * cols + col]
                r2 = rooms[row * cols + col + 1]
                for x, y in self._l_tiles(
                    r1[0] + r1[2] // 2, r1[1] + r1[3] // 2,
                    r2[0] + r2[2] // 2, r2[1] + r2[3] // 2,
                    True,
                ):
                    if 0 <= y < _MAP_H and 0 <= x < _MAP_W:
                        grid[y][x] = '.'

        # Vertical corridors between rows
        for col in range(cols):
            r1 = rooms[col]
            r2 = rooms[cols + col]
            for x, y in self._l_tiles(
                r1[0] + r1[2] // 2, r1[1] + r1[3] // 2,
                r2[0] + r2[2] // 2, r2[1] + r2[3] // 2,
                False,
            ):
                if 0 <= y < _MAP_H and 0 <= x < _MAP_W:
                    grid[y][x] = '.'

        return grid, rooms

    def _fallback_level(
        self, player: Entity
    ) -> tuple[list[list[str]], list[tuple[int, int, int, int]], int, int, int, int]:
        grid, rooms = self._minimal_fallback()
        self.room_types = {i: RoomType.EMPTY for i in range(len(rooms))}
        self.special_features = {}
        self.has_tension_room = False

        up_room, dn_room = rooms[0], rooms[-1]
        up_x = up_room[0] + up_room[2] // 2
        up_y = up_room[1] + up_room[3] // 2
        dn_x = dn_room[0] + dn_room[2] // 2
        dn_y = dn_room[1] + dn_room[3] // 2
        grid[up_y][up_x] = '<'
        grid[dn_y][dn_x] = '>'

        player.x, player.y = up_x, up_y
        self.map = grid
        self.rooms = rooms
        return grid, rooms, up_x, up_y, dn_x, dn_y


# ------------------------------------------------------------------
# Module-level helpers (shared by map_generator and tests)
# ------------------------------------------------------------------

def _straight(x1: int, y1: int, x2: int, y2: int) -> Iterator[tuple[int, int]]:
    if x1 == x2:
        step = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + step, step):
            yield x1, y
    else:
        step = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step, step):
            yield x, y1


def _in_room(x: int, y: int, rooms: list[tuple[int, int, int, int]]) -> bool:
    return any(rx <= x < rx + rw and ry <= y < ry + rh for rx, ry, rw, rh in rooms)


def _bpoint(
    room: tuple[int, int, int, int], tx: int, ty: int
) -> tuple[int, int]:
    rx, ry, rw, rh = room
    return max(rx, min(rx + rw - 1, tx)), max(ry, min(ry + rh - 1, ty))


def _bdist(
    r1: tuple[int, int, int, int], r2: tuple[int, int, int, int]
) -> float:
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    hg = max(0, x2 - (x1 + w1), x1 - (x2 + w2))
    vg = max(0, y2 - (y1 + h1), y1 - (y2 + h2))
    return float(hg + vg)
