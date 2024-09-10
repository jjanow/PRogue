import curses
import heapq
import random
import sys
from classes.entity import Entity
from classes.item import Item, Equipment
from classes.map_generator import MapGenerator
from classes.item_loader import all_items, all_consumables, all_equipment
from curses import KEY_NPAGE, KEY_PPAGE  # Add this import at the top of the file
from classes.input_handler import InputHandler
from classes.renderer import Renderer
from classes.combat_system import CombatSystem
from classes.item import Equipment

class Game:
    def __init__(self, height, width, stdscr):
        self.height = height
        self.width = width
        self.stdscr = stdscr
        self.screen_height, self.screen_width = stdscr.getmaxyx()
        self.map_generator = MapGenerator(height, width, self.screen_height, self.screen_width)
        self.map, self.rooms = self.map_generator.generate()
        self.player = Entity(width // 2, height // 2, '@', "Player", 100, 10, 0)
        self.player.initialize_player()
        self.enemies = []
        self.inventory_page = 0
        self.items_per_page = 26  # Change this to 26 (a-z)
        self.items = []
        self.messages = []
        self.turn_count = 0
        self.last_spawn_turn = 0
        self.dungeon_level = 1
        self.stairs_x = None
        self.stairs_y = None
        self.stairs_up_x = None
        self.stairs_up_y = None
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
        self.spawn_items()
        self.time = 0
        self.selected_slot = None
        self.debug_mode = False

    def open_character_stats_screen(self):
        self.character_stats_mode = True

    def spawn_item_in_inventory(self):
        item = self.create_random_item()
        self.player.add_item(item)
        self.messages.append(f"Spawned {item.name} in your inventory.")

    def spawn_items(self, num_items=None):
        if num_items is None:
            # Reduce the number of items spawned by 50%
            num_items = max(1, (5 + self.dungeon_level) // 2)
        for _ in range(num_items):
            x, y = self.get_random_floor()
            item = self.create_random_item()
            item.x, item.y = x, y
            self.items.append(item)

    def create_random_item(self):
        item_template = random.choice(all_items)
        if isinstance(item_template, Equipment):
            return Equipment(item_template.name, item_template.char, item_template.slot, item_template.stat_boost)
        else:
            return Item(item_template.name, item_template.char, item_template.effect)

    def combat(self, attacker, defender):
        defeated = self.combat_system.combat(attacker, defender, self.messages)
        if defeated:
            if defender in self.enemies:
                self.enemies.remove(defender)
                dropped_item = self.combat_system.player_attack_enemy(attacker, defender, self.messages)
                if dropped_item:
                    self.items.append(dropped_item)
                    self.messages.append(f"{defender.name} dropped a {dropped_item.name}!")
            elif defender == self.player:
                self.messages.append("Game Over!")
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
        elif key == ord('I'):
            self.backpack_mode = True
            self.backpack_page = 0
        elif key == ord('d'):
            self.drop_mode = True
            self.backpack_page = 0
        elif key == ord('@'):
            self.open_character_stats_screen()
        elif key == ord('Q'):
            return self.input_handler.handle_quit()
        elif key == ord('!'):  # Ensure this line is present
            self.input_handler.handle_debug_input(key)
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
        self.map, self.rooms, self.stairs_up_x, self.stairs_up_y, self.stairs_x, self.stairs_y = self.map_generator.generate_level(self.player)        
        self.spawn_enemies(len(self.rooms))
        self.spawn_items()

    def spawn_enemies(self, num_enemies):
        for _ in range(num_enemies):
            x, y = self.get_random_floor()
            difficulty_factor = min(2, 1 + (self.dungeon_level - 1) * 0.1)
            health = int((random.randint(20, 40) + self.dungeon_level * 5) * difficulty_factor)
            damage = int((random.randint(5, 10) + self.dungeon_level) * difficulty_factor)
            defense = int((random.randint(0, 3) + self.dungeon_level // 2) * difficulty_factor)
            enemy = Entity(x, y, 'E', f"Enemy Lv{self.dungeon_level}", health, damage, defense)
            if random.random() < 0.3:
                enemy.add_item(Item("Health Potion", '!', lambda e: setattr(e, 'health', min(e.max_health, e.health + 20))))
            self.enemies.append(enemy)

    def get_random_floor(self):
        while True:
            x = random.randint(0, self.map_generator.width - 1)
            y = random.randint(0, self.map_generator.height - 1)
            if self.map[y][x] == '.' and not any(e.x == x and e.y == y for e in self.enemies):
                return x, y

    def is_valid_move(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.map[y][x] in ['.', '>', '<']

    def process_turn(self):
        # Remove any defeated enemies
        self.enemies = [enemy for enemy in self.enemies if enemy.health > 0]
        
        self.move_enemies()
        self.turn_count += 1
        
        if self.turn_count % 10 == 0:
            heal_amount = min(self.player.max_health - self.player.health, 1)
            self.player.health += heal_amount
            if heal_amount > 0:
                self.messages.append(f"You feel a bit better. (+{heal_amount} HP)")

        if self.turn_count - self.last_spawn_turn >= 50:
            self.spawn_enemies(1)
            self.last_spawn_turn = self.turn_count
        
        # Check for items on the floor (only if not already in messages)
        for item in self.items:
            if item.x == self.player.x and item.y == self.player.y:
                message = f"Floor: {item.name}"
                if message not in self.messages:
                    self.messages.append(message)

        self.player.update_temporary_boosts()

    def check_collisions(self):
        for item in self.items[:]:
            if item.x == self.player.x and item.y == self.player.y:
                self.player.add_item(item)
                self.items.remove(item)
                self.messages.append(f"You picked up {item.name}.")

    def move_enemies(self):
        for enemy in self.enemies:
            if self.distance(enemy, self.player) <= 1:
                self.combat(enemy, self.player)
            else:
                path = self.find_path(enemy, self.player)
                if path and len(path) > 1:
                    next_pos = path[1]  # The next position in the path
                    if not any(e.x == next_pos[0] and e.y == next_pos[1] for e in self.enemies):
                        enemy.x, enemy.y = next_pos

    def next_level(self):
        self.dungeon_level += 1
        self.messages.append(f"You descend to dungeon level {self.dungeon_level}.")
        self.enemies.clear()
        self.items.clear()
        self.generate_level()
    
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

    def use_item(self, item):
        if item in self.player.inventory:
            effect_result = item.effect(self.player)
            self.player.remove_item(item)
            self.messages.append(f"You used {item.name}. {effect_result}")
        else:
            self.messages.append(f"You don't have {item.name}")

    def equip_item(self, item):
        result = self.player.equip(item)
        self.messages.append(result)
    
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
            self.items.append(item)
            self.messages.append(f"You dropped {item.name}.")
            self.drop_mode = False
        else:
            self.messages.append("Invalid item.")

    def drop_backpack_item(self, item_key):
        inventory_items = self.player.get_inventory_items()
        index = ord(item_key) - ord('a') + self.backpack_page * self.items_per_page
        if 0 <= index < len(inventory_items):
            item, _ = inventory_items[index]
            self.player.remove_item(item)
            item.x, item.y = self.player.x, self.player.y
            self.items.append(item)
            self.messages.append(f"You dropped {item.name}.")
            self.drop_mode = False
        else:
            self.messages.append("Invalid item.")

    def get_key(self):
        # This method should be implemented to get a key press from the user
        # For now, we'll just return a placeholder value
        return ord('A')
    
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
        if direction == 'down' and self.player.x == self.stairs_x and self.player.y == self.stairs_y:
            self.next_level()
        elif direction == 'up' and self.player.x == self.stairs_up_x and self.player.y == self.stairs_up_y:
            if self.dungeon_level > 1:
                self.previous_level()
            else:
                self.exit_game()
    
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

    def use_stairs(self, direction):
        if direction == 'down' and self.player.x == self.stairs_x and self.player.y == self.stairs_y:
            self.next_level()
        elif direction == 'up' and self.player.x == self.stairs_up_x and self.player.y == self.stairs_up_y:
            if self.dungeon_level > 1:
                self.previous_level()
            else:
                self.exit_game()
        else:
            self.messages.append("There are no stairs here.")
    
    def wait_for_key(self):
        # This method should be implemented to wait for a key press
        # For now, we'll just pass
        pass
    
    def next_level(self):
        self.dungeon_level += 1
        self.messages.append(f"You descend to dungeon level {self.dungeon_level}.")
        self.enemies.clear()
        self.items.clear()
        self.generate_level()

    def previous_level(self):
        self.dungeon_level -= 1
        self.messages.append(f"You ascend to dungeon level {self.dungeon_level}.")
        self.enemies.clear()
        self.items.clear()
        self.generate_level()
        # Place the player on the down stairs of the previous level
        self.player.x, self.player.y = self.stairs_x, self.stairs_y
    
    def heuristic(self, a, b):
        return abs(b.x - a[0]) + abs(b.y - a[1])
        
    def find_path(self, start, goal):
        start_pos = (start.x, start.y)
        goal_pos = (goal.x, goal.y)

        neighbors = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        close_set = set()
        came_from = {}
        gscore = {start_pos: 0}
        fscore = {start_pos: self.heuristic(start_pos, goal)}
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
                    if neighbor in close_set:
                        continue

                    tentative_g_score = gscore[current] + 1

                    if neighbor not in [i[1] for i in open_heap]:
                        heapq.heappush(open_heap, (fscore.get(neighbor, float('inf')), neighbor))
                    elif tentative_g_score >= gscore.get(neighbor, float('inf')):
                        continue

                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score
                    fscore[neighbor] = gscore[neighbor] + self.heuristic(neighbor, goal)

        return None

    def distance(self, entity1, entity2):
        return max(abs(entity1.x - entity2.x), abs(entity1.y - entity2.y))
    
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
            self.handle_input(key)
            self.render()
            self.display_messages()  # Ensure this method is called to display messages
