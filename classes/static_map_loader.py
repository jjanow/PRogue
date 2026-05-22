import json
from pathlib import Path


class StaticMapLoader:
    """Loads hand-crafted maps from JSON files.

    Map format (data/maps/<name>.json):
      - "tiles"    : list of equal-length strings; each char is a tile.
      - "legend"   : optional dict mapping source chars to
                     {"tile": "<actual tile char>", "tag": "<spawn tag>"}.
                     A char absent from the legend passes through unchanged.
                     A char whose "tile" key is omitted keeps the source char.
      - "fov_mode" : "outdoor" (one giant room — full open visibility) or
                     "dungeon" (supply explicit room rects via "rooms").
      - "rooms"    : optional list of [x, y, w, h] rects; used when
                     fov_mode is "dungeon" and you want hand-placed rooms.
      - "name"     : display name shown in the status bar.

    Standard tile chars (same as the procedural dungeon):
      '#'  wall          '.'  floor         '+'  door
      '<'  stairs up     '>'  stairs down
      'T'  tree (impassable, rendered green)
      '~'  water (impassable, rendered blue)

    Any char in the legend with a "tag" becomes a named spawn point returned
    in the spawns dict.  Common tags:
      "player_start"      — where the player appears on map load
      "dungeon_entrance"  — the tile the player uses to enter the dungeon

    Example legend entry:
      "@": {"tile": ".", "tag": "player_start"}
    """

    def load(self, path):
        """Parse a static map file.

        Returns
        -------
        map_grid : list[list[str]]
            2-D grid of tile characters, all rows the same length.
        rooms : list[tuple[int, int, int, int]]
            (x, y, w, h) room rectangles used by the FOV system.
            For outdoor maps this is a single rect covering the interior.
        spawns : dict[str, tuple[int, int]]
            Maps spawn-tag strings to (x, y) coordinates.
        metadata : dict
            "name" and "fov_mode" from the file header.
        """
        with open(path) as f:
            data = json.load(f)

        raw_rows = data.get("tiles", [])
        legend = data.get("legend", {})

        map_grid = []
        spawns = {}

        for y, row_str in enumerate(raw_rows):
            map_row = []
            for x, ch in enumerate(row_str):
                entry = legend.get(ch)
                if entry is not None:
                    tile_char = entry.get("tile", ch)
                    tag = entry.get("tag")
                    if tag:
                        spawns[tag] = (x, y)
                else:
                    tile_char = ch
                map_row.append(tile_char)
            map_grid.append(map_row)

        # Ensure every row is the same width (pad short rows with walls).
        if map_grid:
            max_w = max(len(row) for row in map_grid)
            for row in map_grid:
                while len(row) < max_w:
                    row.append("#")

        fov_mode = data.get("fov_mode", "dungeon")

        if fov_mode == "outdoor" and map_grid:
            h = len(map_grid)
            w = len(map_grid[0]) if map_grid else 0
            # One giant room covering the entire interior so the FOV system
            # grants full open-air visibility everywhere in town.
            rooms = [(1, 1, w - 2, h - 2)]
        else:
            rooms = [tuple(r) for r in data.get("rooms", [])]

        # Auto-register any untagged stair tiles so callers can find them.
        if "dungeon_entrance" not in spawns:
            for y, row in enumerate(map_grid):
                for x, ch in enumerate(row):
                    if ch == ">":
                        spawns.setdefault("dungeon_entrance", (x, y))

        metadata = {
            "name": data.get("name", "Unknown"),
            "fov_mode": fov_mode,
            "enemy_spawning": data.get("enemy_spawning", True),
        }

        return map_grid, rooms, spawns, metadata
