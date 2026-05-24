from __future__ import annotations
import curses
import heapq
import random
import sys
import time
from collections import deque
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from classes.entity import Entity
from classes.item import Item, Equipment
from classes.map_generator import MapGenerator, RoomType
from classes.static_map_loader import StaticMapLoader
from classes.item_loader import (
    all_consumables,
    all_equipment,
    all_materials,
)
from curses import KEY_NPAGE, KEY_PPAGE
from classes.input_handler import InputHandler
from classes.renderer import Renderer
from classes.combat_system import CombatSystem
from classes.monster_loader import MonsterTemplate, all_monsters
from classes.save_manager import SaveManager, SaveInfo
from classes.systems.ai_system import AISystem
from classes.systems.status_system import StatusSystem
from classes.systems.turn_system import TurnSystem

_TOWN_MAP_PATH = Path(__file__).parent.parent / "data" / "maps" / "town.json"

# Type alias for the flow field: (distance_map, predecessor_map)
_FlowField = tuple[
    dict[tuple[int, int], int],
    dict[tuple[int, int], tuple[int, int] | None],
]


class Game:
    def __init__(self, height: int, width: int, stdscr: curses.window | None) -> None:
        self.height: int = height
        self.width: int = width
        self.stdscr: curses.window | None = stdscr
        if stdscr is not None:
            self.screen_height: int
            self.screen_width: int
            self.screen_height, self.screen_width = stdscr.getmaxyx()
        else:
            self.screen_height = height
            self.screen_width = width
        self.map_generator = MapGenerator(self.screen_height, self.screen_width)
        self.map: list[list[str]] = []
        self.rooms: list[tuple[int, int, int, int]] = []
        self.player = Entity(width // 2, height // 2, '@', "Player", 100, 0, 0)
        self.player.initialize_player()
        self.enemies: list[Entity] = []
        self.inventory_page: int = 0
        self.items_per_page: int = 26
        self.items: list[Item] = []
        self.messages: list[str] = []
        self.turn_count: int = 0
        self.last_spawn_turn: int = 0
        self.in_town: bool = True
        self.dungeon_level: int = 0
        self.stairs_x: int | None = None
        self.stairs_y: int | None = None
        self.stairs_up_x: int | None = None
        self.stairs_up_y: int | None = None
        self.visible: list[list[bool]] = []
        self.explored: list[list[bool]] = []
        self._town_explored: list[list[bool]] | None = None
        self._town_items: list[Item] = []
        self.allow_enemy_spawning: bool = True
        self.generate_level()
        self.inventory_page = 0
        self.inventory_mode: bool = False
        self.character_screen_mode: bool = False
        self.character_stats_mode: bool = False
        self.equipment_mode: bool = False
        self.equipment_slot: str | None = None
        self.backpack_mode: bool = False
        self.backpack_page: int = 0
        self.drop_mode: bool = False
        self.input_handler = InputHandler(self)
        self.renderer = Renderer(self)
        self.combat_system = CombatSystem()
        self.ai_system = AISystem()
        self.status_system = StatusSystem()
        self.turn_system = TurnSystem(self.ai_system, self.status_system)
        self.time: int = 0
        self.selected_slot: int | None = None
        self.debug_mode: bool = False
        self.quit: bool = False
        self.game_over: bool = False
        self.walk_mode: bool = False
        self.auto_explore_mode: bool = False
        self.options_mode: bool = False
        self.walk_speed: int = 5
        self.help_mode: bool = False
        self.speed_input: str = ""
        self.combat_stats_mode: bool = False
        self.save_manager = SaveManager()
        self.save_mode: bool = False
        self.load_mode: bool = False
        self.delete_mode: bool = False
        self.save_load_menu_mode: bool = False
        self.save_slot: int | None = None
        self.save_info_cache: list[SaveInfo] | None = None
        self.open_mode: bool = False
        self.close_mode: bool = False
        self.rest_mode: bool = False
        self.start_time: float = time.time()
        self._flow_field: _FlowField | None = None

    @classmethod
    def create_minimal(cls, height: int, width: int, stdscr: curses.window | None) -> Game:
        """Create a minimal game instance for loading saves without generating content."""
        game = cls.__new__(cls)
        game.height = height
        game.width = width
        game.stdscr = stdscr
        if stdscr is not None:
            game.screen_height, game.screen_width = stdscr.getmaxyx()
        else:
            game.screen_height = height
            game.screen_width = width

        game.player = Entity(width // 2, height // 2, '@', "Player", 100, 0, 0)
        game.player.initialize_player()

        game.enemies = []
        game.items = []
        game.messages = []
        game.rooms = []
        game.map = []
        game.visible = []
        game.explored = []

        game.turn_count = 0
        game.last_spawn_turn = 0
        game.in_town = False
        game.dungeon_level = 1
        game._town_explored = None
        game._town_items = []
        game.allow_enemy_spawning = True
        game.stairs_x = None
        game.stairs_y = None
        game.stairs_up_x = None
        game.stairs_up_y = None
        game.inventory_page = 0
        game.items_per_page = 26
        game.inventory_mode = False
        game.character_screen_mode = False
        game.character_stats_mode = False
        game.equipment_mode = False
        game.equipment_slot = None
        game.backpack_mode = False
        game.backpack_page = 0
        game.drop_mode = False
        game.time = 0
        game.selected_slot = None
        game.debug_mode = False
        game.quit = False
        game.game_over = False
        game.walk_mode = False
        game.auto_explore_mode = False
        game.options_mode = False
        game.walk_speed = 5
        game.help_mode = False
        game.speed_input = ""
        game.combat_stats_mode = False
        game.save_manager = SaveManager()
        game.save_mode = False
        game.load_mode = False
        game.delete_mode = False
        game.save_load_menu_mode = False
        game.save_slot = None
        game.save_info_cache = None
        game.open_mode = False
        game.close_mode = False
        game.rest_mode = False
        game.start_time = time.time()
        game._flow_field = None

        game.map_generator = MapGenerator(game.screen_height, game.screen_width)
        game.input_handler = InputHandler(game)
        game.renderer = Renderer(game)
        game.combat_system = CombatSystem()
        game.ai_system = AISystem()
        game.status_system = StatusSystem()
        game.turn_system = TurnSystem(game.ai_system, game.status_system)

        return game

    def _serialize_rooms(self, rooms: list[tuple[int, int, int, int]]) -> list[list[int]]:
        return [list(room) for room in rooms]

    def _deserialize_rooms(self, serialized_rooms: list[list[int]]) -> list[tuple[int, int, int, int]]:
        return [
            (int(r[0]), int(r[1]), int(r[2]), int(r[3]))
            for r in serialized_rooms
        ]

    def open_character_stats_screen(self) -> None:
        self.character_stats_mode = True

    def open_combat_stats_screen(self) -> None:
        self.combat_stats_mode = True

    def spawn_item_in_inventory(self) -> None:
        item = self.create_random_item()
        self.player.add_item(item)
        self.messages.append(f"Spawned {item.name} in your inventory.")

    def spawn_items(self, num_items: int | None = None) -> None:
        if num_items is None:
            num_items = max(1, (5 + self.dungeon_level) // 2)
        for _ in range(num_items):
            pos = self.get_random_floor()
            if not pos:
                break
            x, y = pos
            item = self.create_random_item()
            item.x, item.y = x, y
            self.items.append(item)

    def create_random_item(self) -> Item:
        ground_loot_pool: list[Item | Equipment] = list(all_consumables) + list(all_equipment)
        item_template = random.choice(ground_loot_pool)
        if isinstance(item_template, Equipment):
            material = random.choice(all_materials)
            name = f"{material.name} {item_template.name}"
            stat = material.power
            return Equipment(
                name,
                item_template.slot,
                item_template.body_part,
                stat,
                damage=item_template.damage,
                ac=item_template.ac,
                accuracy_bonus=item_template.accuracy_bonus,
                weight=item_template.weight,
                material_type=material.name,
                gold_value=item_template.gold_value * material.value_multiplier,
            )
        else:
            return Item(
                item_template.name,
                item_template.effect,
                value=getattr(item_template, "value", None),
                weight=item_template.weight,
                effect_type=getattr(item_template, "effect_type", None),
                gold_value=item_template.gold_value,
                material_type=item_template.material_type,
            )

    def create_specific_item(self, category: str) -> Item | None:
        if category == 'potion':
            if not all_consumables:
                self.messages.append("Error: No consumables available.")
                return None
            template: Item | Equipment = random.choice(all_consumables)
        else:
            if category == 'ring':
                pool: list[Equipment] = [e for e in all_equipment if e.slot.startswith('ring')]
            else:
                pool = [e for e in all_equipment if e.slot == category]
            if not pool:
                if not all_equipment:
                    self.messages.append(f"Error: No equipment available for category '{category}' and no equipment loaded.")
                    return None
                pool = list(all_equipment)
                self.messages.append(f"Warning: No specific items found for '{category}', using random equipment.")
            template = random.choice(pool)

        if isinstance(template, Equipment):
            material = random.choice(all_materials)
            name = f"{material.name} {template.name}"
            stat = material.power
            return Equipment(
                name,
                template.slot,
                template.body_part,
                stat,
                damage=template.damage,
                ac=template.ac,
                accuracy_bonus=template.accuracy_bonus,
                weight=template.weight,
                material_type=material.name,
                gold_value=template.gold_value * material.value_multiplier,
            )
        else:
            return Item(
                template.name,
                template.effect,
                value=getattr(template, "value", None),
                weight=template.weight,
                effect_type=getattr(template, "effect_type", None),
                gold_value=template.gold_value,
                material_type=template.material_type,
            )

    def map_current_level(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                self.explored[y][x] = True
        self.messages.append("The layout of the area reveals itself.")

    def level_up_player(self) -> None:
        previous_level = self.player.level
        self.player.gain_xp(self.player.xp_to_next_level)
        if self.player.level > previous_level:
            self.messages.append(f"You reach level {self.player.level}!")

    def combat(self, attacker: Entity, defender: Entity) -> bool:
        defeated = self.combat_system.combat(attacker, defender, self.messages)

        if defeated:
            if defender in self.enemies:
                self.enemies.remove(defender)

                dropped_items: list[Item] = []
                if attacker == self.player:
                    dropped_items = self.combat_system.player_attack_enemy(attacker, defender, self.messages)

                for item in dropped_items:
                    self.items.append(item)
                    self.messages.append(f"{defender.name} dropped a {item.name}!")
            elif defender == self.player:
                self.handle_player_death()

        if attacker == self.player:
            self.process_turn()

        return defeated

    def handle_input(self, key: int) -> bool:
        if self.inventory_mode:
            self.input_handler.handle_inventory_input(key)
        elif self.backpack_mode:
            self.handle_backpack_input(key)
        elif self.drop_mode:
            self.handle_drop_input(key)
        elif self.character_screen_mode:
            self.input_handler.handle_character_screen_input(key)
        elif self.character_stats_mode:
            self.input_handler.handle_character_stats_input(key)
        elif key == ord('i'):
            self.inventory_mode = True
            self.inventory_page = 0
        elif key == ord('d'):
            self.drop_mode = True
            self.backpack_page = 0
        elif key == ord('@'):
            self.open_character_stats_screen()
        elif key == ord('Q'):
            return self.input_handler.handle_quit()
        else:
            self.input_handler.handle_input(key)
        return False

    def handle_backpack_input(self, key: int) -> None:
        inventory_items = self.player.get_inventory_items()
        max_pages = (len(inventory_items) - 1) // self.items_per_page

        if key == 27:
            self.backpack_mode = False
        elif key in [ord('+'), ord('='), KEY_NPAGE]:
            self.backpack_page = min(self.backpack_page + 1, max_pages)
        elif key in [ord('-'), KEY_PPAGE]:
            self.backpack_page = max(0, self.backpack_page - 1)
        elif 97 <= key <= 122:
            self.use_backpack_item(chr(key))

    def handle_drop_input(self, key: int) -> None:
        inventory_items = self.player.get_inventory_items()
        max_pages = (len(inventory_items) - 1) // self.items_per_page

        if key == 27:
            self.drop_mode = False
        elif key in [ord('+'), ord('='), KEY_NPAGE]:
            self.backpack_page = min(self.backpack_page + 1, max_pages)
        elif key in [ord('-'), KEY_PPAGE]:
            self.backpack_page = max(0, self.backpack_page - 1)
        elif 97 <= key <= 122:
            self.drop_backpack_item(chr(key))

    def draw(self, stdscr: curses.window) -> None:
        self.renderer.draw(stdscr)

    def draw_inventory(self, stdscr: curses.window) -> None:
        self.renderer.draw_inventory(stdscr)

    def draw_character_screen(self, stdscr: curses.window) -> None:
        self.renderer.draw_character_screen(stdscr)

    def draw_equipment_screen(self, stdscr: curses.window) -> None:
        self.renderer.draw_equipment_screen(stdscr)

    def draw_drop_interface(self, stdscr: curses.window) -> None:
        self.renderer.draw_drop_interface(stdscr)

    def generate_level(self) -> None:
        if self.in_town:
            self._load_town_map()
        else:
            self._generate_random_level()

    def _load_town_map(self) -> None:
        loader = StaticMapLoader()
        self.map, self.rooms, spawns, meta = loader.load(_TOWN_MAP_PATH)
        self.height = len(self.map)
        self.width = len(self.map[0]) if self.map else 0

        self.allow_enemy_spawning = bool(meta.get("enemy_spawning", True))

        if "player_start" in spawns:
            self.player.x, self.player.y = spawns["player_start"]

        if "dungeon_entrance" in spawns:
            self.stairs_x, self.stairs_y = spawns["dungeon_entrance"]
        else:
            self.stairs_x = self.stairs_y = None

        self.stairs_up_x = None
        self.stairs_up_y = None

        self.visible = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.explored = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.invalidate_flow_field()
        self.update_fov()
        if self.allow_enemy_spawning:
            self.spawn_enemies(len(self.rooms))

    def _generate_random_level(self) -> None:
        self.allow_enemy_spawning = True
        self.map, self.rooms, self.stairs_up_x, self.stairs_up_y, self.stairs_x, self.stairs_y = \
            self.map_generator.generate_level(self.player, self.dungeon_level)
        self.height = len(self.map)
        self.width = len(self.map[0]) if self.map else 0
        self.visible = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.explored = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.invalidate_flow_field()
        self.update_fov()
        self._spawn_by_content_types()
        self._spawn_ambient()

    def enter_dungeon(self) -> None:
        import copy
        self._town_explored = copy.deepcopy(self.explored)
        self._town_items = list(self.items)
        self.in_town = False
        self.dungeon_level = 1
        self.messages.append("You descend into the depths of the dungeon...")
        self.enemies.clear()
        self.items.clear()
        self.generate_level()

    def return_to_town(self) -> None:
        self.in_town = True
        self.dungeon_level = 0
        self.messages.append("You climb out of the dungeon and return to Millhaven.")
        self.enemies.clear()
        self.items.clear()
        self.generate_level()
        if self._town_explored is not None:
            self.explored = self._town_explored
            self._town_explored = None
            self.update_fov()
        self.items = list(self._town_items)
        self._town_items = []
        if self.stairs_x is not None:
            self.player.x, self.player.y = self.stairs_x, self.stairs_y  # type: ignore[assignment]

    def get_monster_template(self) -> MonsterTemplate:
        min_cr = max(0.1, (self.dungeon_level - 1) * 0.5)
        max_cr = self.dungeon_level * 0.5 + 0.5
        candidates = [m for m in all_monsters if min_cr <= m.challenge_rating <= max_cr]
        if not candidates:
            candidates = list(all_monsters)
        return random.choice(candidates)

    def _make_enemy(self, x: int, y: int) -> Entity:
        """Create a level-appropriate enemy at (x, y)."""
        template = self.get_monster_template()
        df = template.challenge_rating
        health = max(3, int((random.randint(20, 40) + self.dungeon_level * 5) * df))
        enemy = Entity(x, y, 'E', template.name, health, 0, 0)
        raw_dmg = max(1, int((random.randint(5, 10) + self.dungeon_level) * df))
        raw_def = int((random.randint(0, 3) + self.dungeon_level // 2) * df)
        enemy.strength = raw_dmg * 2
        enemy.dexterity = max(1, raw_def * 3)
        enemy.constitution = max(1, raw_def * 2)
        enemy.level = max(1, round(template.challenge_rating * 2))
        enemy.xp_reward = template.xp
        enemy.gold_reward = template.gold
        enemy.loot = template.create_loot()
        return enemy

    def _get_room_floor(
        self, room: tuple[int, int, int, int]
    ) -> list[tuple[int, int]]:
        rx, ry, rw, rh = room
        return [
            (rx + dx, ry + dy)
            for dy in range(rh)
            for dx in range(rw)
            if self.map[ry + dy][rx + dx] == '.'
            and not any(e.x == rx + dx and e.y == ry + dy for e in self.enemies)
            and (rx + dx, ry + dy) != (self.player.x, self.player.y)
        ]

    def _spawn_by_content_types(self) -> None:
        mg = self.map_generator
        tension_warned = False
        for idx, rtype in mg.room_types.items():
            room = self.rooms[idx]
            if rtype == RoomType.MONSTER_DEN:
                self._spawn_den(room)
            elif rtype == RoomType.TREASURE:
                self._spawn_treasure(room)
            elif rtype == RoomType.TENSION:
                self._spawn_tension(room)
                if not tension_warned:
                    self.messages.append("You sense a certain tension.")
                    tension_warned = True

    def _spawn_den(self, room: tuple[int, int, int, int]) -> None:
        template = self.get_monster_template()
        df = template.challenge_rating
        count = random.randint(2, 4)
        tiles = self._get_room_floor(room)
        random.shuffle(tiles)
        for x, y in tiles[:count]:
            health = max(3, int((random.randint(20, 40) + self.dungeon_level * 5) * df))
            enemy = Entity(x, y, 'E', template.name, health, 0, 0)
            raw_dmg = max(1, int((random.randint(5, 10) + self.dungeon_level) * df))
            raw_def = int((random.randint(0, 3) + self.dungeon_level // 2) * df)
            enemy.strength = raw_dmg * 2
            enemy.dexterity = max(1, raw_def * 3)
            enemy.constitution = max(1, raw_def * 2)
            enemy.level = max(1, round(template.challenge_rating * 2))
            enemy.xp_reward = template.xp
            enemy.gold_reward = template.gold
            enemy.loot = template.create_loot()
            self.enemies.append(enemy)

    def _spawn_treasure(self, room: tuple[int, int, int, int]) -> None:
        tiles = self._get_room_floor(room)
        random.shuffle(tiles)
        for x, y in tiles[:random.randint(2, 4)]:
            item = self.create_random_item()
            item.x, item.y = x, y
            self.items.append(item)

    def _spawn_tension(self, room: tuple[int, int, int, int]) -> None:
        tiles = self._get_room_floor(room)
        random.shuffle(tiles)
        count = max(2, min(5, len(tiles) // 5))
        for x, y in tiles[:count]:
            self.enemies.append(self._make_enemy(x, y))

    def _spawn_ambient(self) -> None:
        """Ambient monster and item spawning outside content rooms."""
        mg = self.map_generator
        content_room_indices = {
            idx for idx, t in mg.room_types.items()
            if t in (RoomType.MONSTER_DEN, RoomType.TENSION, RoomType.TREASURE, RoomType.SHOP)
        }
        content_room_tiles = {
            (rx + dx, ry + dy)
            for idx in content_room_indices
            for rx, ry, rw, rh in [self.rooms[idx]]
            for dy in range(rh)
            for dx in range(rw)
        }

        # Count traversable tiles for monster budget
        traversable = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.map[y][x] in ('.', '+', '<', '>', '^', 'A', '~', 'f', 'b', '/')
        ]
        monster_budget = len(traversable) // 45
        item_budget = len(traversable) // 35

        # Corridor tiles + empty/special room tiles for monsters
        monster_tiles = [
            (x, y) for (x, y) in traversable
            if self.map[y][x] == '.'
            and (x, y) not in content_room_tiles
            and not any(e.x == x and e.y == y for e in self.enemies)
            and (x, y) != (self.player.x, self.player.y)
        ]
        random.shuffle(monster_tiles)
        for x, y in monster_tiles[:monster_budget]:
            self.enemies.append(self._make_enemy(x, y))

        # Room interior tiles (non-content rooms) for items
        room_tiles = [
            (x, y)
            for idx, (rx, ry, rw, rh) in enumerate(self.rooms)
            if idx not in content_room_indices
            for dy in range(rh)
            for dx in range(rw)
            for x, y in [(rx + dx, ry + dy)]
            if self.map[y][x] == '.'
        ]
        random.shuffle(room_tiles)
        for x, y in room_tiles[:item_budget]:
            item = self.create_random_item()
            item.x, item.y = x, y
            self.items.append(item)

    def spawn_enemies(self, num_enemies: int) -> None:
        for _ in range(num_enemies):
            pos = self.get_random_floor()
            if not pos:
                break
            x, y = pos
            template = self.get_monster_template()
            difficulty_factor = template.challenge_rating
            health = max(3, int((random.randint(20, 40) + self.dungeon_level * 5) * difficulty_factor))
            enemy = Entity(x, y, 'E', template.name, health, 0, 0)

            raw_damage = max(1, int((random.randint(5, 10) + self.dungeon_level) * difficulty_factor))
            raw_defense = int((random.randint(0, 3) + self.dungeon_level // 2) * difficulty_factor)

            enemy.strength = raw_damage * 2
            enemy.dexterity = max(1, raw_defense * 3)
            enemy.constitution = max(1, raw_defense * 2)
            enemy.level = max(1, round(template.challenge_rating * 2))
            enemy.xp_reward = template.xp
            enemy.gold_reward = template.gold
            enemy.loot = template.create_loot()
            self.enemies.append(enemy)

    def get_random_floor(self, max_attempts: int = 1000) -> tuple[int, int] | None:
        """Return coordinates of a random walkable tile or ``None`` if none are available."""
        for _ in range(max_attempts):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (
                self.map[y][x] == '.'
                and (x, y) != (self.player.x, self.player.y)
                and not any(e.x == x and e.y == y for e in self.enemies)
            ):
                return x, y
        return None

    def is_valid_move(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height and self.map[y][x] in ['.', '>', '<', '/', '^', 'A', '~', 'f', 'b']

    def invalidate_flow_field(self) -> None:
        self._flow_field = None

    def _compute_flow_field(self) -> None:
        """BFS from the player outward; stores (distance, predecessor) per tile."""
        px, py = self.player.x, self.player.y
        passable = {'.', '<', '>', '+', '/', '^', 'A', '~', 'f', 'b'}
        dist: dict[tuple[int, int], int] = {(px, py): 0}
        prev: dict[tuple[int, int], tuple[int, int] | None] = {(px, py): None}
        queue: deque[tuple[int, int]] = deque([(px, py)])
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        while queue:
            x, y = queue.popleft()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in dist and 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.map[ny][nx] in passable:
                        dist[(nx, ny)] = dist[(x, y)] + 1
                        prev[(nx, ny)] = (x, y)
                        queue.append((nx, ny))
        self._flow_field = (dist, prev)

    def get_flow_field(self) -> _FlowField:
        if self._flow_field is None:
            self._compute_flow_field()
        assert self._flow_field is not None
        return self._flow_field

    def get_flow_next_step(self, enemy: Entity) -> tuple[int, int] | None:
        """Return the next tile the enemy should move to in order to approach the player."""
        dist, _ = self.get_flow_field()
        ex, ey = enemy.x, enemy.y
        occupied = {(e.x, e.y) for e in self.enemies if e is not enemy and e.health > 0}
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        current_dist: float = dist.get((ex, ey), float('inf'))
        best: tuple[int, int] | None = None
        for dx, dy in directions:
            nx, ny = ex + dx, ey + dy
            if (nx, ny) in occupied:
                continue
            nd: float = dist.get((nx, ny), float('inf'))
            if nd < current_dist:
                current_dist = nd
                best = (nx, ny)
        return best

    def process_turn(self) -> None:
        self.turn_system.process(self)  # type: ignore[arg-type]

    def check_collisions(self) -> None:
        for item in self.items[:]:
            if item.x == self.player.x and item.y == self.player.y:
                self.player.add_item(item)
                self.items.remove(item)
                self.messages.append(f"You picked up {item.name}.")

    def next_level(self) -> None:
        self.dungeon_level += 1
        self.messages.append(f"You descend to dungeon level {self.dungeon_level}.")
        self.enemies.clear()
        self.items.clear()
        self._generate_random_level()

    def open_inventory(self) -> None:
        self.inventory_mode = True
        self.inventory_page = 0

    def pickup_item(self) -> None:
        for item in self.items:
            if item.x == self.player.x and item.y == self.player.y:
                self.player.add_item(item)
                self.items.remove(item)
                self.messages.append(f"You picked up a {item.name}.")
                return
        self.messages.append("There's nothing here to pick up.")

    def use_backpack_item(self, item_key: str) -> None:
        inventory_items = self.player.get_inventory_items()
        index = ord(item_key) - ord('a') + self.backpack_page * self.items_per_page
        if 0 <= index < len(inventory_items):
            item, _ = inventory_items[index]
            if isinstance(item, Equipment):
                self.equip_item(item)
            else:
                self.use_item(item)
        else:
            self.messages.append("Invalid item.")

    def drop_backpack_item(self, item_key: str) -> None:
        inventory_items = self.player.get_inventory_items()
        index = ord(item_key) - ord('a') + self.backpack_page * self.items_per_page
        if 0 <= index < len(inventory_items):
            item, _ = inventory_items[index]
            self.player.remove_item(item)
            item.x, item.y = self.player.x, self.player.y
            item.seen = True
            self.items.append(item)
            self.messages.append(f"You dropped {item.name}.")
            self.drop_mode = False
        else:
            self.messages.append("Invalid item.")

    def get_key(self) -> int:
        return ord('A')

    def display_messages(self) -> None:
        """Output queued messages to the standard screen and clear them."""
        if self.stdscr:
            for i, message in enumerate(self.messages[-3:]):
                self.stdscr.addstr(self.screen_height - 3 + i, 0, str(message)[:self.screen_width - 1])
            self.stdscr.refresh()
        else:
            for message in self.messages:
                print(message)
        self.messages.clear()

    def use_or_equip_item(self, key: str) -> None:
        inventory_items = self.player.get_inventory_items()
        index = ord(key) - ord('a')
        if 0 <= index < len(inventory_items):
            item, _ = inventory_items[index]
            if isinstance(item, Equipment):
                self.equip_item(item)
            else:
                self.use_item(item)

    def open_character_screen(self) -> None:
        self.character_screen_mode = True

    def use_stairs(self, direction: str) -> None:
        if self.in_town:
            if direction == 'down' and self.stairs_x is not None and \
                    self.player.x == self.stairs_x and self.player.y == self.stairs_y:
                self.enter_dungeon()
            elif direction == 'up':
                self.messages.append("There are no stairs leading up here.")
        else:
            if direction == 'down' and self.player.x == self.stairs_x and self.player.y == self.stairs_y:
                self.next_level()
            elif direction == 'up' and self.player.x == self.stairs_up_x and self.player.y == self.stairs_up_y:
                if self.dungeon_level > 1:
                    self.previous_level()
                else:
                    self.return_to_town()

    def walk_to(self, x: int, y: int, animate: bool = False) -> bool:
        """Automatically walk the player to the given coordinates using pathfinding.

        Returns True if the walk was interrupted by user input."""
        target_pos = (x, y)
        player_pos = (self.player.x, self.player.y)
        dist, prev = self.get_flow_field()

        path: list[tuple[int, int]]
        if target_pos not in dist:
            target = type('Target', (object,), {'x': x, 'y': y})()
            raw_path = self.find_path(self.player, target)
            if not raw_path or len(raw_path) < 2:
                self.messages.append("No path to destination.")
                return False
            path = raw_path
        else:
            path = [target_pos]
            current_pos: tuple[int, int] = target_pos
            ok = True
            while current_pos != player_pos:
                next_step = prev.get(current_pos)
                if next_step is None:
                    ok = False
                    break
                path.append(next_step)
                current_pos = next_step
            if ok:
                path.reverse()
            else:
                target = type('Target', (object,), {'x': x, 'y': y})()
                raw_path = self.find_path(self.player, target)
                if not raw_path or len(raw_path) < 2:
                    self.messages.append("No path to destination.")
                    return False
                path = raw_path

        interrupted = False
        draw_steps = animate and self.stdscr is not None and self.walk_speed > 0
        check_keys = animate and self.stdscr is not None

        if check_keys and self.stdscr is not None:
            self.stdscr.nodelay(True)

        try:
            for step in path[1:]:
                if check_keys and self.stdscr is not None:
                    key = self.stdscr.getch()
                    if key != -1:
                        curses.ungetch(key)
                        interrupted = True
                        break

                dx = step[0] - self.player.x
                dy = step[1] - self.player.y
                prev_x, prev_y = self.player.x, self.player.y
                self.player_move_or_attack(dx, dy)

                if self.quit:
                    interrupted = True
                    break

                if any(self.visible[e.y][e.x] for e in self.enemies):
                    self.messages.append("Monster spotted!")
                    interrupted = True
                    break

                if draw_steps and self.stdscr is not None:
                    self.renderer.draw(self.stdscr)
                    time.sleep(self.walk_speed / 1000.0)

                if (self.player.x, self.player.y) == (prev_x, prev_y):
                    break
                if (self.player.x, self.player.y) == (x, y):
                    break
        finally:
            if check_keys and self.stdscr is not None:
                self.stdscr.nodelay(False)

        if animate and not draw_steps and self.stdscr is not None:
            self.renderer.draw(self.stdscr)

        return interrupted

    def walk_to_stairs(self, direction: str) -> None:
        if direction == 'up':
            if self.stairs_up_x is not None:
                self.walk_to(self.stairs_up_x, self.stairs_up_y, animate=True)  # type: ignore[arg-type]
            else:
                self.messages.append("There are no stairs leading up here.")
        elif direction == 'down':
            if self.stairs_x is not None:
                self.walk_to(self.stairs_x, self.stairs_y, animate=True)  # type: ignore[arg-type]

    def find_nearest_unexplored(self) -> tuple[int, int] | None:
        """Return coordinates of the nearest tile that will reveal unexplored areas."""
        start = (self.player.x, self.player.y)
        heap: list[tuple[int, tuple[int, int]]] = [(0, start)]
        visited: set[tuple[int, int]] = set()

        while heap:
            d, (x, y) = heapq.heappop(heap)
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if (x, y) != start:
                if not self.explored[y][x]:
                    return (x, y)

                for dx, dy in [
                    (-1, 0), (1, 0), (0, -1), (0, 1),
                    (-1, -1), (1, -1), (-1, 1), (1, 1)
                ]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if not self.explored[ny][nx]:
                            return (x, y)

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                           (-1, -1), (1, -1), (-1, 1), (1, 1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                        self.map[ny][nx] in ['.', '<', '>', '+', '/', '^', 'A', '~', 'f', 'b'] and
                        (nx, ny) not in visited):
                    heapq.heappush(heap, (d + 1, (nx, ny)))
        return None

    def auto_explore(self) -> None:
        """Automatically explore the dungeon until a monster is seen."""
        self.auto_explore_mode = True
        attempts_without_progress = 0
        max_attempts = 10

        while self.auto_explore_mode and attempts_without_progress < max_attempts:
            if self.quit:
                break
            if any(self.visible[e.y][e.x] for e in self.enemies):
                self.messages.append("Monster spotted!")
                break

            target = self.find_nearest_unexplored()
            if not target:
                self.messages.append("Nothing left to explore.")
                break

            start_x, start_y = self.player.x, self.player.y

            interrupted = self.walk_to(target[0], target[1], animate=True)
            if interrupted:
                break

            if (self.player.x, self.player.y) == (start_x, start_y):
                attempts_without_progress += 1
                self.process_turn()
            else:
                attempts_without_progress = 0

        if attempts_without_progress >= max_attempts:
            self.messages.append("Auto-explore stopped: no progress made.")

        self.auto_explore_mode = False

    def rest_until_healed(self) -> None:
        p = self.player
        if p.health >= p.max_health and p.mana >= p.max_mana and p.psi >= p.max_psi:
            self.messages.append("You are already fully rested.")
            return

        if any(self.visible[e.y][e.x] for e in self.enemies):
            self.messages.append("You cannot rest with enemies nearby.")
            return

        self.messages.append("You begin to rest...")
        self.rest_mode = True

        if self.stdscr:
            self.stdscr.nodelay(True)

        try:
            last_health = p.health
            last_mana = p.mana
            last_psi = p.psi
            last_msg_count = len(self.messages)
            need_draw = True

            while True:
                p = self.player

                if p.health >= p.max_health and p.mana >= p.max_mana and p.psi >= p.max_psi:
                    self.messages.append("You wake feeling fully rested.")
                    need_draw = True
                    break

                if any(self.visible[e.y][e.x] for e in self.enemies):
                    self.messages.append("Your rest is interrupted by a nearby enemy!")
                    need_draw = True
                    break

                if self.stdscr:
                    key = self.stdscr.getch()
                    if key != -1:
                        self.messages.append("Rest interrupted.")
                        need_draw = True
                        break

                health_before = p.health

                self.process_turn()

                if p.health < health_before:
                    self.messages.append("Your rest is interrupted!")
                    need_draw = True
                    break

                if self.quit:
                    break

                if self.turn_count % 10 == 0:
                    if p.mana < p.max_mana:
                        p.mana = min(p.max_mana, p.mana + 1)
                    if p.psi < p.max_psi:
                        p.psi = min(p.max_psi, p.psi + 1)

                if (p.health != last_health or p.mana != last_mana or
                        p.psi != last_psi or len(self.messages) != last_msg_count):
                    need_draw = True
                    last_health = p.health
                    last_mana = p.mana
                    last_psi = p.psi
                    last_msg_count = len(self.messages)

                if self.stdscr and need_draw:
                    self.renderer.draw(self.stdscr)
                    need_draw = False

            if self.stdscr and need_draw:
                self.renderer.draw(self.stdscr)
        finally:
            self.rest_mode = False
            if self.stdscr:
                self.stdscr.nodelay(False)

    def exit_game(self) -> None:
        try:
            total_value: float = sum(
                item.stat_boost for item in self.player.inventory if isinstance(item, Equipment)
            )
            total_value += sum(
                slot['item'].stat_boost for slot in self.player.equipment.values() if slot['item']
            )
            total_value += self.player.money
        except AttributeError as e:
            self.messages.append(f"Error calculating total value: {str(e)}")
            total_value = 0

        self.messages.append(f"Congratulations! You've escaped the dungeon with treasure worth {total_value} gold!")
        self.messages.append("Press any key to exit.")
        self.wait_for_key()
        sys.exit()

    def wait_for_key(self) -> None:
        if self.stdscr:
            self.stdscr.nodelay(False)
            self.stdscr.getch()
        else:
            try:
                input()
            except EOFError:
                pass

    def handle_player_death(self) -> None:
        """Handle player death by setting the quit flag and truncating health."""
        self.player.health = max(0, self.player.health)
        self.messages.append("Game Over! Press Enter to exit.")
        self.quit = True
        self.game_over = True

    def previous_level(self) -> None:
        self.dungeon_level -= 1
        self.messages.append(f"You ascend to dungeon level {self.dungeon_level}.")
        self.enemies.clear()
        self.items.clear()
        self._generate_random_level()
        self.player.x, self.player.y = self.stairs_x, self.stairs_y  # type: ignore[assignment]

    def heuristic(self, a: tuple[int, int], b: Any) -> int:
        bx: int
        by: int
        bx, by = (b.x, b.y) if hasattr(b, "x") else b
        return abs(bx - a[0]) + abs(by - a[1])

    def find_path(
        self,
        start: Any,
        goal: Any,
        consider_enemies: bool = False,
    ) -> list[tuple[int, int]] | None:
        start_pos: tuple[int, int] = (start.x, start.y) if hasattr(start, "x") else start
        goal_pos: tuple[int, int] = (goal.x, goal.y) if hasattr(goal, "x") else goal

        avoid: set[tuple[int, int]] = set()
        if consider_enemies:
            avoid = {
                (e.x, e.y)
                for e in self.enemies
                if (e.x, e.y) != start_pos and (e.x, e.y) != goal_pos and e.health > 0
            }

        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        close_set: set[tuple[int, int]] = set()
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        gscore: dict[tuple[int, int], float] = {start_pos: 0}
        fscore: dict[tuple[int, int], float] = {start_pos: self.heuristic(start_pos, goal_pos)}
        open_heap: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_heap, (fscore[start_pos], start_pos))

        while open_heap:
            current = heapq.heappop(open_heap)[1]
            if current == goal_pos:
                path: list[tuple[int, int]] = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_pos)
                path.reverse()
                return path

            close_set.add(current)

            for i, j in neighbors:
                neighbor: tuple[int, int] = (current[0] + i, current[1] + j)
                if 0 <= neighbor[0] < self.width and 0 <= neighbor[1] < self.height:
                    if self.map[neighbor[1]][neighbor[0]] in ['#', ' ']:
                        continue
                    if neighbor in close_set or neighbor in avoid:
                        continue

                    tentative_g_score = gscore[current] + 1

                    if tentative_g_score < gscore.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        gscore[neighbor] = tentative_g_score
                        fscore[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_pos)
                        heapq.heappush(open_heap, (fscore[neighbor], neighbor))

        return None

    def distance(self, entity1: Entity, entity2: Entity) -> int:
        return max(abs(entity1.x - entity2.x), abs(entity1.y - entity2.y))

    def line(self, x1: int, y1: int, x2: int, y2: int) -> Iterator[tuple[int, int]]:
        """Yield points on a Bresenham line from (x1, y1) to (x2, y2)."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = 1 if x2 > x1 else -1
        sy = 1 if y2 > y1 else -1

        if dx > dy:
            err = dx / 2.0
            while x != x2:
                yield x, y
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y2:
                yield x, y
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        yield x2, y2

    def in_room(self, x: int, y: int) -> bool:
        """Return True if the coordinates are inside any generated room."""
        for rx, ry, w, h in self.rooms:
            if rx <= x < rx + w and ry <= y < ry + h:
                return True
        return False

    def get_room(self, x: int, y: int) -> tuple[int, int, int, int] | None:
        """Return the room tuple containing (x, y) or None if not in a room."""
        for room in self.rooms:
            rx, ry, w, h = room
            if rx <= x < rx + w and ry <= y < ry + h:
                return room
        return None

    def corridor_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Return the number of corridor tiles between leaving the starting room and reaching (x2, y2)."""
        distance: float = 0
        left_room = False
        for px, py in self.line(x1, y1, x2, y2):
            if (px, py) == (x1, y1):
                continue
            if self.in_room(px, py):
                if left_room:
                    return float('inf')
            else:
                if not left_room:
                    left_room = True
                distance += 1
            if (px, py) == (x2, y2):
                break
        return distance

    def has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Return True if there is a clear line of sight between two points."""
        prev_x, prev_y = x1, y1
        for x, y in self.line(x1, y1, x2, y2):
            if (x, y) == (x1, y1):
                continue
            if x != prev_x and y != prev_y and (x, y) != (x2, y2):
                if self.map[prev_y][x] == '#' and self.map[y][prev_x] == '#':
                    return False
            if (x, y) != (x2, y2) and self.map[y][x] in ('#', '+'):
                return False
            prev_x, prev_y = x, y
        return True

    def update_fov(self, radius: int | None = None) -> None:
        """Update which tiles are visible using line of sight and mark them as explored."""
        px, py = self.player.x, self.player.y
        player_room = self.get_room(px, py)
        player_in_room = player_room is not None

        if radius is None:
            radius = 3 if not player_in_room else max(self.width, self.height)
        else:
            if not player_in_room:
                radius = min(radius, 3)

        self.visible = [[False for _ in range(self.width)] for _ in range(self.height)]

        for y in range(max(0, py - radius), min(self.height, py + radius + 1)):
            for x in range(max(0, px - radius), min(self.width, px + radius + 1)):
                if max(abs(px - x), abs(py - y)) > radius:
                    continue

                if not self.has_line_of_sight(px, py, x, y):
                    continue

                target_room = self.get_room(x, y)

                if player_in_room:
                    if target_room is None:
                        if self.corridor_distance(px, py, x, y) > 2:
                            continue
                    elif target_room != player_room:
                        continue

                self.visible[y][x] = True
                self.explored[y][x] = True

        for item in self.items:
            if 0 <= item.y < self.height and 0 <= item.x < self.width:  # type: ignore[operator]
                if self.visible[item.y][item.x]:  # type: ignore[index]
                    item.seen = True

    def open_equipment_screen(self) -> None:
        self.equipment_mode = True
        self.equipment_slot = None

    def equip_item(self, item_key: str | Equipment) -> None:
        eq_item: Equipment
        if isinstance(item_key, str):
            inventory_items = self.player.get_inventory_items()
            index = ord(item_key) - ord('a')
            if not (0 <= index < len(inventory_items)):
                self.messages.append("Invalid item.")
                return
            raw_item, _ = inventory_items[index]
            if not isinstance(raw_item, Equipment):
                self.messages.append(f"{raw_item.name} is not equippable.")
                return
            eq_item = raw_item
        else:
            eq_item = item_key

        message = self.player.equip_item(eq_item)
        self.messages.append(message)

    def unequip_item(self, slot_key: str) -> None:
        message = self.player.unequip_item(slot_key)
        self.messages.append(message)

    def use_item(self, item: Item) -> None:
        if item in self.player.inventory:
            effect_result = item.effect(self.player) if item.effect is not None else None
            self.player.remove_item(item)
            self.messages.append(f"You used {item.name}. {effect_result}")
        else:
            self.messages.append(f"You don't have {item.name}")

    def player_move_or_attack(self, dx: int, dy: int) -> None:
        new_x, new_y = self.player.x + dx, self.player.y + dy
        if not (0 <= new_x < self.width and 0 <= new_y < self.height):
            return
        enemy_at_position = next((e for e in self.enemies if e.x == new_x and e.y == new_y), None)

        if enemy_at_position:
            self.combat(self.player, enemy_at_position)
        elif self.map[new_y][new_x] == '+':
            self.map[new_y][new_x] = '/'
            self.messages.append("You open the door.")
            self.invalidate_flow_field()
            self.update_fov()
            self.process_turn()
        elif self.is_valid_move(new_x, new_y):
            self.player.x, self.player.y = new_x, new_y
            self.invalidate_flow_field()
            if self.map[new_y][new_x] == '^':
                dmg = random.randint(1, 6)
                self.player.health -= dmg
                self.messages.append(f"You triggered a trap! -{dmg} HP")
                self.map[new_y][new_x] = '.'
            self.process_turn()

    def open_door(self, dx: int, dy: int) -> None:
        tx, ty = self.player.x + dx, self.player.y + dy
        if not (0 <= tx < self.width and 0 <= ty < self.height):
            self.messages.append("There is no door there.")
            return
        if self.map[ty][tx] == '+':
            self.map[ty][tx] = '/'
            self.messages.append("You open the door.")
            self.invalidate_flow_field()
            self.update_fov()
            self.process_turn()
        elif self.map[ty][tx] == '/':
            self.messages.append("The door is already open.")
        else:
            self.messages.append("There is no door there.")

    def close_door(self, dx: int, dy: int) -> None:
        tx, ty = self.player.x + dx, self.player.y + dy
        if not (0 <= tx < self.width and 0 <= ty < self.height):
            self.messages.append("There is no door there.")
            return
        if self.map[ty][tx] == '/':
            if any(e.x == tx and e.y == ty for e in self.enemies):
                self.messages.append("Something is blocking the door.")
                return
            self.map[ty][tx] = '+'
            self.messages.append("You close the door.")
            self.invalidate_flow_field()
            self.update_fov()
            self.process_turn()
        elif self.map[ty][tx] == '+':
            self.messages.append("The door is already closed.")
        else:
            self.messages.append("There is no door there.")

    def handle_equipment_input(self, key: int) -> None:
        if key in range(ord('a'), ord('m') + 1):
            slot_key = chr(key)
            slot = self.player.equipment[slot_key]
            equippable_items = [
                item for item in self.player.inventory
                if isinstance(item, Equipment) and item.slot == slot['name']
            ]

            if equippable_items:
                item_to_equip = equippable_items[0]
                result = self.player.equip(item_to_equip, slot_key)
                self.messages.append(result)
            else:
                self.messages.append(f"No items to equip in {slot['name']} slot")
        elif key == ord('q'):
            self.equipment_mode = False

    def gain_xp(self, amount: int) -> None:
        self.player.gain_xp(amount)

    def gain_gold(self, amount: int) -> None:
        self.player.money += amount

    def game_loop(self) -> None:
        while not self.quit:
            key = self.get_key()
            if self.handle_input(key):
                self.quit = True
                break
            if hasattr(self, 'renderer') and self.stdscr is not None:
                self.renderer.draw(self.stdscr)
            self.display_messages()
