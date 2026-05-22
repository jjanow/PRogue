import curses
import heapq
import random
import sys
import time
from collections import deque
from pathlib import Path
from classes.entity import Entity
from classes.item import Item, Equipment
from classes.map_generator import MapGenerator
from classes.static_map_loader import StaticMapLoader
from classes.item_loader import (
    all_items,
    all_consumables,
    all_equipment,
    all_materials,
)
from curses import KEY_NPAGE, KEY_PPAGE
from classes.input_handler import InputHandler
from classes.renderer import Renderer
from classes.combat_system import CombatSystem
from classes.monster_loader import all_monsters
from classes.save_manager import SaveManager
from classes.systems.ai_system import AISystem
from classes.systems.status_system import StatusSystem
from classes.systems.turn_system import TurnSystem

_TOWN_MAP_PATH = Path(__file__).parent.parent / "data" / "maps" / "town.json"

class Game:
    def __init__(self, height, width, stdscr):
        self.height = height
        self.width = width
        self.stdscr = stdscr
        self.screen_height, self.screen_width = stdscr.getmaxyx()
        # MapGenerator is kept for random dungeon levels; not used in town.
        self.map_generator = MapGenerator(height, width, self.screen_height, self.screen_width)
        self.map = []
        self.rooms = []
        # Player starts with no inherent damage or defense; stats and gear scale these
        self.player = Entity(width // 2, height // 2, '@', "Player", 100, 0, 0)
        self.player.initialize_player()
        self.enemies = []
        self.inventory_page = 0
        self.items_per_page = 26
        self.items = []
        self.messages = []
        self.turn_count = 0
        self.last_spawn_turn = 0
        self.in_town = True   # start in the overworld town
        self.dungeon_level = 0
        self.stairs_x = None
        self.stairs_y = None
        self.stairs_up_x = None
        self.stairs_up_y = None
        self.visible = []
        self.explored = []
        # Town state preserved across dungeon trips
        self._town_explored = None   # cached FOV exploration grid
        self._town_items = []        # cached ground items left in town
        self.allow_enemy_spawning = True  # overwritten by map metadata on load
        self.generate_level()
        self.inventory_page = 0
        self.inventory_mode = False
        self.character_screen_mode = False
        self.character_stats_mode = False
        self.equipment_mode = False
        self.equipment_slot = None
        self.backpack_mode = False
        self.backpack_page = 0
        self.drop_mode = False
        self.input_handler = InputHandler(self)
        self.renderer = Renderer(self)
        self.combat_system = CombatSystem()
        self.ai_system = AISystem()
        self.status_system = StatusSystem()
        self.turn_system = TurnSystem(self.ai_system, self.status_system)
        self.time = 0
        self.selected_slot = None
        self.debug_mode = False
        self.quit = False
        self.game_over = False
        self.walk_mode = False
        self.auto_explore_mode = False
        self.options_mode = False
        self.walk_speed = 5  # milliseconds between auto-move steps
        self.help_mode = False
        self.speed_input = ""
        self.combat_stats_mode = False
        self.save_manager = SaveManager()
        self.save_mode = False
        self.load_mode = False
        self.delete_mode = False
        self.save_load_menu_mode = False
        self.save_slot = None
        self.save_info_cache = None
        self.start_time = time.time()
        self.path_cache = {}

    @classmethod
    def create_minimal(cls, height, width, stdscr):
        """Create a minimal game instance for loading saves without generating content."""
        game = cls.__new__(cls)
        game.height = height
        game.width = width
        game.stdscr = stdscr
        game.screen_height, game.screen_width = stdscr.getmaxyx()
        
        # Create minimal player (will be overwritten by save data)
        game.player = Entity(width // 2, height // 2, '@', "Player", 100, 0, 0)
        game.player.initialize_player()
        
        # Initialize empty containers
        game.enemies = []
        game.items = []
        game.messages = []
        game.rooms = []
        game.map = []
        game.visible = []
        game.explored = []
        
        # Initialize game state variables
        game.turn_count = 0
        game.last_spawn_turn = 0
        game.in_town = False  # overwritten from save
        game.dungeon_level = 1
        game._town_explored = None
        game._town_items = []
        game.allow_enemy_spawning = True  # overwritten from save
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
        game.start_time = time.time()
        game.path_cache = {}
        
        # Initialize systems
        game.input_handler = InputHandler(game)
        game.renderer = Renderer(game)
        game.combat_system = CombatSystem()
        game.ai_system = AISystem()
        game.status_system = StatusSystem()
        game.turn_system = TurnSystem(game.ai_system, game.status_system)

        return game

    def _serialize_rooms(self, rooms):
        """Serialize rooms for saving."""
        return [list(room) for room in rooms]
    
    def _deserialize_rooms(self, serialized_rooms):
        """Deserialize rooms from save data."""
        return [tuple(room) for room in serialized_rooms]

    def open_character_stats_screen(self):
        self.character_stats_mode = True

    def open_combat_stats_screen(self):
        self.combat_stats_mode = True

    def spawn_item_in_inventory(self):
        item = self.create_random_item()
        self.player.add_item(item)
        self.messages.append(f"Spawned {item.name} in your inventory.")

    def spawn_items(self, num_items=None):
        if num_items is None:
            # Reduce the number of items spawned by 50%
            num_items = max(1, (5 + self.dungeon_level) // 2)
        for _ in range(num_items):
            pos = self.get_random_floor()
            if not pos:
                break
            x, y = pos
            item = self.create_random_item()
            item.x, item.y = x, y
            self.items.append(item)

    def create_random_item(self):
        # Exclude misc items from ground loot - they should only drop from monsters
        ground_loot_pool = all_consumables + all_equipment
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

    def create_specific_item(self, category):
        if category == 'potion':
            if not all_consumables:
                self.messages.append("Error: No consumables available.")
                return None
            template = random.choice(all_consumables)
        else:
            if category == 'ring':
                pool = [e for e in all_equipment if e.slot.startswith('ring')]
            else:
                pool = [e for e in all_equipment if e.slot == category]
            if not pool:
                # Fallback to all equipment if no specific category found
                if not all_equipment:
                    self.messages.append(f"Error: No equipment available for category '{category}' and no equipment loaded.")
                    return None
                pool = all_equipment
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

    def map_current_level(self):
        for y in range(self.height):
            for x in range(self.width):
                self.explored[y][x] = True
        self.messages.append("The layout of the area reveals itself.")

    def level_up_player(self):
        previous_level = self.player.level
        self.player.gain_xp(self.player.xp_to_next_level)
        if self.player.level > previous_level:
            self.messages.append(f"You reach level {self.player.level}!")

    def combat(self, attacker, defender):
        defeated = self.combat_system.combat(attacker, defender, self.messages)

        if defeated:
            if defender in self.enemies:
                self.enemies.remove(defender)

                dropped_items = []
                if attacker == self.player:
                    dropped_items = self.combat_system.player_attack_enemy(attacker, defender, self.messages)

                for item in dropped_items:
                    self.items.append(item)
                    self.messages.append(
                        f"{defender.name} dropped a {item.name}!"
                    )
            elif defender == self.player:
                self.handle_player_death()

        if attacker == self.player:
            self.process_turn()

        return defeated

    def handle_input(self, key):
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
        return False  # Don't exit the game

    def handle_backpack_input(self, key):
        inventory_items = self.player.get_inventory_items()
        max_pages = (len(inventory_items) - 1) // self.items_per_page

        if key == 27:  # ESC key
            self.backpack_mode = False
        elif key in [ord('+'), ord('='), KEY_NPAGE]:
            self.backpack_page = min(self.backpack_page + 1, max_pages)
        elif key in [ord('-'), KEY_PPAGE]:
            self.backpack_page = max(0, self.backpack_page - 1)
        elif 97 <= key <= 122:  # a-z
            self.use_backpack_item(chr(key))

    def handle_drop_input(self, key):
        inventory_items = self.player.get_inventory_items()
        max_pages = (len(inventory_items) - 1) // self.items_per_page

        if key == 27:  # ESC key
            self.drop_mode = False
        elif key in [ord('+'), ord('='), KEY_NPAGE]:
            self.backpack_page = min(self.backpack_page + 1, max_pages)
        elif key in [ord('-'), KEY_PPAGE]:
            self.backpack_page = max(0, self.backpack_page - 1)
        elif 97 <= key <= 122:  # a-z
            self.drop_backpack_item(chr(key))

    def draw(self, stdscr):
        self.renderer.draw(stdscr)

    def draw_inventory(self, stdscr):
        self.renderer.draw_inventory(stdscr)

    def draw_character_screen(self, stdscr):
        self.renderer.draw_character_screen(stdscr)

    def draw_equipment_screen(self, stdscr):
        self.renderer.draw_equipment_screen(stdscr)

    def draw_drop_interface(self, stdscr):
        self.renderer.draw_drop_interface(stdscr)

    def generate_level(self):
        if self.in_town:
            self._load_town_map()
        else:
            self._generate_random_level()

    def _load_town_map(self):
        loader = StaticMapLoader()
        self.map, self.rooms, spawns, meta = loader.load(_TOWN_MAP_PATH)
        self.height = len(self.map)
        self.width = len(self.map[0]) if self.map else 0

        self.allow_enemy_spawning = meta.get("enemy_spawning", True)

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
        self.update_fov()
        if self.allow_enemy_spawning:
            self.spawn_enemies(len(self.rooms))

    def _generate_random_level(self):
        self.allow_enemy_spawning = True
        self.map, self.rooms, self.stairs_up_x, self.stairs_up_y, self.stairs_x, self.stairs_y = \
            self.map_generator.generate_level(self.player)
        self.height = len(self.map)
        self.width = len(self.map[0]) if self.map else 0
        self.visible = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.explored = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.update_fov()
        self.spawn_enemies(len(self.rooms))
        self.spawn_items()

    def enter_dungeon(self):
        import copy
        # Preserve town state so it is intact when the player returns.
        self._town_explored = copy.deepcopy(self.explored)
        self._town_items = list(self.items)
        self.in_town = False
        self.dungeon_level = 1
        self.messages.append("You descend into the depths of the dungeon...")
        self.enemies.clear()
        self.items.clear()
        self.generate_level()

    def return_to_town(self):
        self.in_town = True
        self.dungeon_level = 0
        self.messages.append("You climb out of the dungeon and return to Millhaven.")
        self.enemies.clear()
        self.items.clear()
        self.generate_level()  # loads fresh town map + FOV
        # Restore exploration and items from before the dungeon trip.
        if self._town_explored is not None:
            self.explored = self._town_explored
            self._town_explored = None
            self.update_fov()  # recalculate visible from restored explored
        self.items = list(self._town_items)
        self._town_items = []
        # Place the player at the dungeon entrance (they climbed out from there).
        if self.stairs_x is not None:
            self.player.x, self.player.y = self.stairs_x, self.stairs_y

    def get_monster_template(self):
        min_cr = max(0.1, (self.dungeon_level - 1) * 0.5)
        max_cr = self.dungeon_level * 0.5 + 0.5
        candidates = [m for m in all_monsters if min_cr <= m.challenge_rating <= max_cr]
        if not candidates:
            candidates = all_monsters
        return random.choice(candidates)

    def spawn_enemies(self, num_enemies):
        for _ in range(num_enemies):
            pos = self.get_random_floor()
            if not pos:
                break
            x, y = pos
            template = self.get_monster_template()
            difficulty_factor = max(1, template.challenge_rating)
            health = int((random.randint(20, 40) + self.dungeon_level * 5) * difficulty_factor)
            enemy = Entity(x, y, 'E', template.name, health, 0, 0)

            raw_damage = int((random.randint(5, 10) + self.dungeon_level) * difficulty_factor)
            raw_defense = int((random.randint(0, 3) + self.dungeon_level // 2) * difficulty_factor)

            enemy.strength = raw_damage * 2
            enemy.dexterity = max(1, raw_defense * 3)
            enemy.constitution = max(1, raw_defense * 2)
            enemy.level = max(1, round(template.challenge_rating * 2))
            enemy.xp_reward = template.xp
            enemy.gold_reward = template.gold
            enemy.loot = template.create_loot()
            self.enemies.append(enemy)

    def get_random_floor(self, max_attempts=1000):
        """Return coordinates of a random walkable tile or ``None`` if none are
        available."""
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

    def is_valid_move(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.map[y][x] in ['.', '>', '<']

    def compute_all_shortest_paths(self):
        """Precompute shortest paths between all walkable tiles on the map."""
        map_height = len(self.map)
        map_width = len(self.map[0]) if self.map else 0
        walkable = [
            (x, y)
            for y in range(map_height)
            for x in range(map_width)
            if self.map[y][x] in ['.', '<', '>']
        ]

        self.path_cache = {}
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]

        for start in walkable:
            queue = deque([start])
            visited = {start}
            prev = {}
            while queue:
                x, y = queue.popleft()
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < map_width and 0 <= ny < map_height and
                        self.map[ny][nx] in ['.', '<', '>'] and
                        (nx, ny) not in visited
                    ):
                        visited.add((nx, ny))
                        prev[(nx, ny)] = (x, y)
                        queue.append((nx, ny))
            self.path_cache[start] = prev

    def get_cached_path(self, start, goal):
        """Return a path from start to goal using the precomputed cache."""
        if hasattr(start, 'x'):
            start = (start.x, start.y)
        if hasattr(goal, 'x'):
            goal = (goal.x, goal.y)

        if start == goal:
            return [start]

        prev = self.path_cache.get(start)
        if not prev or goal not in prev:
            return None

        path = [goal]
        current = goal
        while current != start:
            current = prev.get(current)
            if current is None:
                return None
            path.append(current)
        path.reverse()
        return path

    def process_turn(self):
        self.turn_system.process(self)

    def check_collisions(self):
        for item in self.items[:]:
            if item.x == self.player.x and item.y == self.player.y:
                self.player.add_item(item)
                self.items.remove(item)
                self.messages.append(f"You picked up {item.name}.")

    def next_level(self):
        self.dungeon_level += 1
        self.messages.append(f"You descend to dungeon level {self.dungeon_level}.")
        self.enemies.clear()
        self.items.clear()
        self._generate_random_level()
    
    def open_inventory(self):
        self.inventory_mode = True
        self.inventory_page = 0
    
    def pickup_item(self):
        for item in self.items:
            if item.x == self.player.x and item.y == self.player.y:
                self.player.add_item(item)
                self.items.remove(item)
                self.messages.append(f"You picked up a {item.name}.")
                return
        self.messages.append("There's nothing here to pick up.")

    def use_backpack_item(self, item_key):
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

    def drop_backpack_item(self, item_key):
        inventory_items = self.player.get_inventory_items()
        index = ord(item_key) - ord('a') + self.backpack_page * self.items_per_page
        if 0 <= index < len(inventory_items):
            item, _ = inventory_items[index]
            self.player.remove_item(item)
            item.x, item.y = self.player.x, self.player.y
            item.seen = True  # Player is aware of dropped items immediately
            self.items.append(item)
            self.messages.append(f"You dropped {item.name}.")
            self.drop_mode = False
        else:
            self.messages.append("Invalid item.")

    def get_key(self):
        # This method should be implemented to get a key press from the user
        # For now, we'll just return a placeholder value
        return ord('A')

    def display_messages(self):
        """Output queued messages to the standard screen and clear them."""
        if self.stdscr:
            for i, message in enumerate(self.messages[-3:]):
                self.stdscr.addstr(self.screen_height - 3 + i, 0, str(message)[:self.screen_width - 1])
            self.stdscr.refresh()
        else:
            for message in self.messages:
                print(message)
        self.messages.clear()
    
    def use_or_equip_item(self, key):
        inventory_items = self.player.get_inventory_items()
        index = ord(key) - ord('a')
        if 0 <= index < len(inventory_items):
            item, _ = inventory_items[index]
            if isinstance(item, Equipment):
                self.equip_item(item)
            else:
                self.use_item(item)
    
    def open_character_screen(self):
        self.character_screen_mode = True

    def use_stairs(self, direction):
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

    def walk_to(self, x, y, animate=False):
        """Automatically walk the player to the given coordinates using pathfinding.

        Returns True if the walk was interrupted by user input."""
        target = type('Target', (object,), {'x': x, 'y': y})()
        path = self.get_cached_path(self.player, target)
        
        # Fallback to find_path if cached path fails
        if not path or len(path) < 2:
            path = self.find_path(self.player, target)
            if not path or len(path) < 2:
                self.messages.append("No path to destination.")
                return False

        interrupted = False
        draw_steps = animate and self.stdscr and self.walk_speed > 0
        check_keys = animate and self.stdscr

        if check_keys:
            self.stdscr.nodelay(True)

        try:
            for step in path[1:]:
                if check_keys:
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

                if draw_steps:
                    self.renderer.draw(self.stdscr)
                    time.sleep(self.walk_speed / 1000.0)

                if (self.player.x, self.player.y) == (prev_x, prev_y):
                    break
                if (self.player.x, self.player.y) == (x, y):
                    break
        finally:
            if check_keys:
                self.stdscr.nodelay(False)

        if animate and not draw_steps and self.stdscr:
            self.renderer.draw(self.stdscr)

        return interrupted

    def walk_to_stairs(self, direction):
        if direction == 'up':
            if self.stairs_up_x is not None:
                self.walk_to(self.stairs_up_x, self.stairs_up_y, animate=True)
            else:
                self.messages.append("There are no stairs leading up here.")
        elif direction == 'down':
            if self.stairs_x is not None:
                self.walk_to(self.stairs_x, self.stairs_y, animate=True)

    def find_nearest_unexplored(self):
        """Return coordinates of the nearest tile that will reveal unexplored
        areas when the player walks there."""
        from heapq import heappush, heappop

        start = (self.player.x, self.player.y)
        heap = [(0, start)]
        visited = set()

        while heap:
            dist, (x, y) = heappop(heap)
            if (x, y) in visited:
                continue
            visited.add((x, y))

            # Never target the starting tile; it won't reveal anything new if
            # unexplored neighbors are blocked by walls or the map edge.
            if (x, y) != start:
                # If this tile itself is unexplored, walking onto it will
                # explore it
                if not self.explored[y][x]:
                    return (x, y)

                # If any adjacent tile is unexplored (including walls), moving
                # here will reveal it via the field of view
                for dx, dy in [
                    (-1, 0), (1, 0), (0, -1), (0, 1),
                    (-1, -1), (1, -1), (-1, 1), (1, 1)
                ]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if not self.explored[ny][nx]:
                            return (x, y)

            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1),
                           (-1,-1), (1,-1), (-1,1), (1,1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                        self.map[ny][nx] in ['.', '<', '>'] and
                        (nx, ny) not in visited):
                    heappush(heap, (dist + 1, (nx, ny)))
        return None

    def auto_explore(self):
        """Automatically explore the dungeon until a monster is seen."""
        self.auto_explore_mode = True
        attempts_without_progress = 0
        max_attempts = 10  # Prevent infinite loops
        
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

            # Store current position to detect if we made progress
            start_x, start_y = self.player.x, self.player.y
            
            interrupted = self.walk_to(target[0], target[1], animate=True)
            if interrupted:
                break
                
            # Check if we actually moved
            if (self.player.x, self.player.y) == (start_x, start_y):
                attempts_without_progress += 1
                # Process a turn if we didn't move to update game state
                self.process_turn()
            else:
                attempts_without_progress = 0
                # No need to process turn here as walk_to already did it

        if attempts_without_progress >= max_attempts:
            self.messages.append("Auto-explore stopped: no progress made.")
            
        self.auto_explore_mode = False
    
    def exit_game(self):
        try:
            total_value = sum(item.stat_boost for item in self.player.inventory if isinstance(item, Equipment))
            total_value += sum(slot['item'].stat_boost for slot in self.player.equipment.values() if slot['item'])
            total_value += self.player.money
        except AttributeError as e:
            self.messages.append(f"Error calculating total value: {str(e)}")
            total_value = 0  # fallback value

        self.messages.append(f"Congratulations! You've escaped the dungeon with treasure worth {total_value} gold!")
        self.messages.append("Press any key to exit.")
        self.wait_for_key()
        sys.exit()

    def wait_for_key(self):
        if self.stdscr:
            self.stdscr.nodelay(False)
            self.stdscr.getch()
        else:
            try:
                input()
            except EOFError:
                pass

    def handle_player_death(self):
        """Handle player death by setting the quit flag and truncating health."""
        self.player.health = max(0, self.player.health)
        self.messages.append("Game Over! Press Enter to exit.")
        self.quit = True
        self.game_over = True
    
    def previous_level(self):
        self.dungeon_level -= 1
        self.messages.append(f"You ascend to dungeon level {self.dungeon_level}.")
        self.enemies.clear()
        self.items.clear()
        self._generate_random_level()
        # Place the player on the down stairs of the previous level
        self.player.x, self.player.y = self.stairs_x, self.stairs_y
    
    def heuristic(self, a, b):
        bx, by = (b.x, b.y) if hasattr(b, "x") else b
        return abs(bx - a[0]) + abs(by - a[1])

    def find_path(self, start, goal, consider_enemies=False):
        start_pos = (start.x, start.y) if hasattr(start, "x") else start
        goal_pos = (goal.x, goal.y) if hasattr(goal, "x") else goal

        avoid = set()
        if consider_enemies:
            avoid = {
                (e.x, e.y)
                for e in self.enemies
                if (e.x, e.y) != start_pos and (e.x, e.y) != goal_pos and e.health > 0
            }

        neighbors = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        close_set = set()
        came_from = {}
        gscore = {start_pos: 0}
        fscore = {start_pos: self.heuristic(start_pos, goal_pos)}
        open_heap = []
        heapq.heappush(open_heap, (fscore[start_pos], start_pos))

        while open_heap:
            current = heapq.heappop(open_heap)[1]
            if current == goal_pos:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_pos)
                path.reverse()
                return path

            close_set.add(current)

            for i, j in neighbors:
                neighbor = current[0] + i, current[1] + j
                if 0 <= neighbor[0] < self.width and 0 <= neighbor[1] < self.height:
                    if self.map[neighbor[1]][neighbor[0]] in ['#', ' ']:
                        continue
                    if neighbor in close_set or neighbor in avoid:
                        continue

                    tentative_g_score = gscore[current] + 1

                    if neighbor not in [n[1] for n in open_heap]:
                        heapq.heappush(open_heap, (fscore.get(neighbor, float('inf')), neighbor))
                    elif tentative_g_score >= gscore.get(neighbor, float('inf')):
                        continue

                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score
                    fscore[neighbor] = gscore[neighbor] + self.heuristic(neighbor, goal_pos)

        return None

    def distance(self, entity1, entity2):
        return max(abs(entity1.x - entity2.x), abs(entity1.y - entity2.y))

    def line(self, x1, y1, x2, y2):
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

    def in_room(self, x, y):
        """Return True if the coordinates are inside any generated room."""
        for rx, ry, w, h in self.rooms:
            if rx <= x < rx + w and ry <= y < ry + h:
                return True
        return False

    def get_room(self, x, y):
        """Return the room tuple containing (x, y) or None if not in a room."""
        for room in self.rooms:
            rx, ry, w, h = room
            if rx <= x < rx + w and ry <= y < ry + h:
                return room
        return None

    def corridor_distance(self, x1, y1, x2, y2):
        """Return the number of corridor tiles between leaving the starting
        room and reaching (x2, y2). Only meaningful if (x1, y1) is inside a
        room and (x2, y2) is outside of it."""
        distance = 0
        left_room = False
        for px, py in self.line(x1, y1, x2, y2):
            if (px, py) == (x1, y1):
                continue
            if self.in_room(px, py):
                if left_room:
                    # LOS passes through another room — treat as unreachable so
                    # the player cannot see corridors on the far side of rooms.
                    return float('inf')
            else:
                if not left_room:
                    left_room = True
                distance += 1
            if (px, py) == (x2, y2):
                break
        return distance

    def has_line_of_sight(self, x1, y1, x2, y2):
        """Return True if there is a clear line of sight between two points."""
        prev_x, prev_y = x1, y1
        for x, y in self.line(x1, y1, x2, y2):
            if (x, y) == (x1, y1):
                continue
            # When the line steps diagonally through an intermediate tile, check
            # both orthogonal neighbors. If both are walls the line is cutting
            # through a tight corner and should be blocked. Skip this check for
            # the destination tile itself — you can see a corner wall, just not
            # through it.
            if x != prev_x and y != prev_y and (x, y) != (x2, y2):
                if self.map[prev_y][x] == '#' and self.map[y][prev_x] == '#':
                    return False
            if (x, y) != (x2, y2) and self.map[y][x] == '#':
                return False
            prev_x, prev_y = x, y
        return True

    def update_fov(self, radius=None):
        """Update which tiles are visible using line of sight and mark them as
        explored. Vision down connecting corridors is limited to two tiles when
        standing in a room, and overall sight is restricted to a 3 tile radius
        when the player is in a hallway."""

        px, py = self.player.x, self.player.y
        player_room = self.get_room(px, py)
        player_in_room = player_room is not None

        if radius is None:
            # Unlimited radius in rooms, but only three tiles while in corridors
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

        # Mark any items within the current field of view as seen so they remain
        # visible on explored tiles even after they leave the player's sight.
        for item in self.items:
            if 0 <= item.y < self.height and 0 <= item.x < self.width:
                if self.visible[item.y][item.x]:
                    item.seen = True
    
    def open_equipment_screen(self):
        self.equipment_mode = True
        self.equipment_slot = None
    
    def equip_item(self, item_key):
        inventory_items = self.player.get_inventory_items()
        
        if isinstance(item_key, str):
            index = ord(item_key) - ord('a')
            if 0 <= index < len(inventory_items):
                item, _ = inventory_items[index]
            else:
                self.messages.append("Invalid item.")
                return
        elif isinstance(item_key, Equipment):
            item = item_key
        else:
            self.messages.append("Invalid item key.")
            return

        if isinstance(item, Equipment):
            message = self.player.equip_item(item)
            self.messages.append(message)
        else:
            self.messages.append(f"{item.name} is not equippable.")

    def unequip_item(self, slot_key):
        message = self.player.unequip_item(slot_key)
        self.messages.append(message)

    def use_item(self, item):
        if item in self.player.inventory:
            effect_result = item.effect(self.player)
            self.player.remove_item(item)
            self.messages.append(f"You used {item.name}. {effect_result}")
        else:
            self.messages.append(f"You don't have {item.name}")

    def player_move_or_attack(self, dx, dy):
        new_x, new_y = self.player.x + dx, self.player.y + dy
        enemy_at_position = next((e for e in self.enemies if e.x == new_x and e.y == new_y), None)

        if enemy_at_position:
            self.combat(self.player, enemy_at_position)
        elif self.is_valid_move(new_x, new_y):
            self.player.x, self.player.y = new_x, new_y
            self.process_turn()

    def handle_equipment_input(self, key):
        if key in range(ord('a'), ord('m') + 1):
            slot_key = chr(key)
            slot = self.player.equipment[slot_key]
            equippable_items = [item for item in self.player.inventory if isinstance(item, Equipment) and item.slot == slot['name']]
            
            if equippable_items:
                item_to_equip = equippable_items[0]  # Choose the first equippable item
                result = self.player.equip(item_to_equip, slot_key)
                self.messages.append(result)
            else:
                self.messages.append(f"No items to equip in {slot['name']} slot")
        elif key == ord('q'):
            self.equipment_mode = False


    def gain_xp(self, amount):
        self.player.gain_xp(amount)

    def gain_gold(self, amount):
        self.player.money += amount
    
    def game_loop(self):
        while not self.quit:
            key = self.get_key()
            if self.handle_input(key):
                self.quit = True
                break
            if hasattr(self, 'renderer') and hasattr(self, 'stdscr'):
                self.renderer.draw(self.stdscr)
            self.display_messages()

