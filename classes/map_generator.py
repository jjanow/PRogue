from __future__ import annotations

import random
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.entity import Entity


class MapGenerator:
    def __init__(self, height: int, width: int, screen_height: int, screen_width: int) -> None:
        self.height = max(10, min(height, screen_height - 6))
        self.width = max(20, min(width, screen_width - 5))
        self.map: list[list[str]] = []
        self.rooms: list[tuple[int, int, int, int]] = []

    def generate(self) -> tuple[list[list[str]], list[tuple[int, int, int, int]]]:
        self.map, self.rooms = self._generate_map_and_rooms()
        return self.map, self.rooms

    # ------------------------------------------------------------------
    # Map construction
    # ------------------------------------------------------------------

    def _generate_map_and_rooms(self, _attempt: int = 0) -> tuple[list[list[str]], list[tuple[int, int, int, int]]]:
        self.map = [['#' for _ in range(self.width)] for _ in range(self.height)]
        rooms: list[tuple[int, int, int, int]] = []

        target = random.randint(4, 8)
        room_h_max = max(3, min(8, (self.height - 2) // 3))
        room_w_max = max(3, min(12, (self.width - 2) // 5))

        for _ in range(300):
            if len(rooms) >= target:
                break

            rh = random.randint(3, room_h_max)
            rw = random.randint(3, room_w_max)

            if self.width - 2 < rw or self.height - 2 < rh:
                continue

            x = random.randint(1, self.width - rw - 1)
            y = random.randint(1, self.height - rh - 1)

            if not any(self._rooms_overlap(x, y, rw, rh, r) for r in rooms):
                self._create_room(x, y, rw, rh)
                rooms.append((x, y, rw, rh))

        # Need at least two rooms; retry up to 5 times with fresh randomness.
        if len(rooms) < 2:
            if _attempt < 5:
                return self._generate_map_and_rooms(_attempt + 1)
            # Absolute fallback: two minimal rooms in opposite corners.
            self.map = [['#' for _ in range(self.width)] for _ in range(self.height)]
            rooms = [(1, 1, 3, 3), (self.width - 4, self.height - 4, 3, 3)]
            for r in rooms:
                self._create_room(*r)

        self._connect_rooms(rooms)
        return self.map, rooms

    def _rooms_overlap(self, x: int, y: int, w: int, h: int, room: tuple[int, int, int, int]) -> bool:
        # Enforces a 1-tile gap: rooms must not share a border tile.
        rx, ry, rw, rh = room
        return (x <= rx + rw and x + w >= rx and
                y <= ry + rh and y + h >= ry)

    def _create_room(self, x: int, y: int, w: int, h: int) -> None:
        for row in range(y, y + h):
            for col in range(x, x + w):
                self.map[row][col] = '.'

    # ------------------------------------------------------------------
    # Corridor connection (Prim's spanning tree)
    # ------------------------------------------------------------------

    def _connect_rooms(self, rooms: list[tuple[int, int, int, int]]) -> None:
        """Connect all rooms via a minimum spanning tree of L-shaped corridors.

        Prefers orientations that avoid traversing a third room's interior.
        Falls back to force-carving if no clean path exists for a given edge."""
        connected: list[tuple[int, int, int, int]] = [rooms[0]]
        unconnected: list[tuple[int, int, int, int]] = list(rooms[1:])

        while unconnected:
            _, rc, ru = min(
                ((self._center_dist(rc, ru), rc, ru)
                 for rc in connected for ru in unconnected),
                key=lambda t: t[0],
            )

            # Try every already-connected room in proximity order.
            for rc_try in sorted(connected, key=lambda r: self._center_dist(r, ru)):
                if self._carve_corridor(rc_try, ru, rooms):
                    break
            else:
                # Last resort: H-then-V regardless of room overlap.
                self._force_carve(rc, ru)

            connected.append(ru)
            unconnected.remove(ru)

    def _center_dist(self, r1: tuple[int, int, int, int], r2: tuple[int, int, int, int]) -> int:
        cx1, cy1 = r1[0] + r1[2] // 2, r1[1] + r1[3] // 2
        cx2, cy2 = r2[0] + r2[2] // 2, r2[1] + r2[3] // 2
        return abs(cx1 - cx2) + abs(cy1 - cy2)

    def _in_other_room(self, x: int, y: int, room_a: tuple[int, int, int, int], room_b: tuple[int, int, int, int], rooms: list[tuple[int, int, int, int]]) -> bool:
        """True if (x, y) falls inside any room that is not room_a or room_b."""
        for r in rooms:
            if r == room_a or r == room_b:
                continue
            rx, ry, rw, rh = r
            if rx <= x < rx + rw and ry <= y < ry + rh:
                return True
        return False

    def _carve_corridor(self, room1: tuple[int, int, int, int], room2: tuple[int, int, int, int], all_rooms: list[tuple[int, int, int, int]]) -> bool:
        """Try H-then-V and V-then-H; carve the first orientation that avoids
        all third rooms.  Returns True if carved, False if both orientations fail."""
        cx1 = room1[0] + room1[2] // 2
        cy1 = room1[1] + room1[3] // 2
        cx2 = room2[0] + room2[2] // 2
        cy2 = room2[1] + room2[3] // 2

        for h_first in (True, False):
            tiles = self._l_tiles(cx1, cy1, cx2, cy2, h_first)
            if not any(
                self._in_other_room(x, y, room1, room2, all_rooms)
                for x, y in tiles
            ):
                for x, y in tiles:
                    self.map[y][x] = '.'
                return True
        return False

    def _force_carve(self, room1: tuple[int, int, int, int], room2: tuple[int, int, int, int]) -> None:
        """Unconditionally carve H-then-V from room1 center to room2 center."""
        cx1 = room1[0] + room1[2] // 2
        cy1 = room1[1] + room1[3] // 2
        cx2 = room2[0] + room2[2] // 2
        cy2 = room2[1] + room2[3] // 2
        for x, y in self._l_tiles(cx1, cy1, cx2, cy2, True):
            self.map[y][x] = '.'

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def _l_tiles(self, x1: int, y1: int, x2: int, y2: int, h_first: bool) -> list[tuple[int, int]]:
        """All tiles on an L-shaped path; corner tile not duplicated."""
        tx, ty = (x2, y1) if h_first else (x1, y2)
        seg1 = list(self._straight(x1, y1, tx, ty))
        seg2 = list(self._straight(tx, ty, x2, y2))
        return seg1 + seg2[1:]

    def _straight(self, x1: int, y1: int, x2: int, y2: int) -> Iterator[tuple[int, int]]:
        """Yield tiles along a purely horizontal or vertical line."""
        if x1 == x2:
            step = 1 if y2 >= y1 else -1
            for y in range(y1, y2 + step, step):
                yield x1, y
        else:
            step = 1 if x2 >= x1 else -1
            for x in range(x1, x2 + step, step):
                yield x, y1

    # ------------------------------------------------------------------
    # Sparse feature placement
    # ------------------------------------------------------------------

    def _in_room(self, x: int, y: int, rooms: list[tuple[int, int, int, int]]) -> bool:
        return any(rx <= x < rx + rw and ry <= y < ry + rh
                   for rx, ry, rw, rh in rooms)

    def _place_doors(self, rooms: list[tuple[int, int, int, int]]) -> None:
        """Place '+' doors at corridor tiles immediately adjacent to room interiors
        with ~50 % probability each."""
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.map[y][x] != '.':
                    continue
                if self._in_room(x, y, rooms):
                    continue
                adj_room = any(
                    self._in_room(x + dx, y + dy, rooms)
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                )
                if adj_room and random.random() < 0.5:
                    self.map[y][x] = '+'

    def _place_traps(self, rooms: list[tuple[int, int, int, int]]) -> None:
        """Scatter 1–3 trap tiles ('^') on random floor tiles."""
        candidates = [
            (x, y)
            for y in range(1, self.height - 1)
            for x in range(1, self.width - 1)
            if self.map[y][x] == '.'
        ]
        random.shuffle(candidates)
        for x, y in candidates[:random.randint(1, 3)]:
            self.map[y][x] = '^'

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate_level(self, player: Entity) -> tuple[list[list[str]], list[tuple[int, int, int, int]], int, int, int, int]:
        self.map, self.rooms = self.generate()

        # Reinforce outer border as solid wall.
        for x in range(self.width):
            self.map[0][x] = '#'
            self.map[self.height - 1][x] = '#'
        for y in range(self.height):
            self.map[y][0] = '#'
            self.map[y][self.width - 1] = '#'

        # Stairs go in the first and last rooms (always separate when ≥ 2 rooms).
        up_room = self.rooms[0]
        down_room = self.rooms[-1]

        stairs_up_x = up_room[0] + up_room[2] // 2
        stairs_up_y = up_room[1] + up_room[3] // 2
        self.map[stairs_up_y][stairs_up_x] = '<'

        stairs_x = down_room[0] + down_room[2] // 2
        stairs_y = down_room[1] + down_room[3] // 2
        self.map[stairs_y][stairs_x] = '>'

        # Doors and traps placed after stairs so they never overwrite stair tiles.
        self._place_doors(self.rooms)
        self._place_traps(self.rooms)

        player.x, player.y = stairs_up_x, stairs_up_y

        return self.map, self.rooms, stairs_up_x, stairs_up_y, stairs_x, stairs_y
