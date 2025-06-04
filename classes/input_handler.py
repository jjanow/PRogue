import curses

from classes.item import Equipment

class InputHandler:
    def __init__(self, game):
        self.game = game

    def handle_input(self, key):
        if self.game.debug_mode:
            self.handle_debug_input(key)
            return False  # Don't exit the game

        if self.game.inventory_mode:
            self.handle_inventory_input(key)
        elif self.game.backpack_mode:
            self.handle_backpack_input(key)
        elif self.game.character_screen_mode:
            self.handle_character_screen_input(key)
        elif self.game.character_stats_mode:
            self.handle_character_stats_input(key)
        elif key == ord('i'):
            self.game.inventory_mode = True
            self.game.inventory_page = 0
        elif key == ord('I'):
            self.game.backpack_mode = True
            self.game.backpack_page = 0
        elif key == ord('@'):
            self.game.open_character_stats_screen()
        elif key == ord('Q'):
            return self.handle_quit()
        else:
            self.handle_main_game_input(key)
        return False  # Don't exit the game

    def handle_main_game_input(self, key):
        if self.game.walk_mode:
            if key == ord('<'):
                if not self.game.explored[self.game.stairs_up_y][self.game.stairs_up_x]:
                    self.game.messages.append("You don't know where the upstairs are.")
                else:
                    self.game.walk_to_stairs('up')
                self.game.walk_mode = False
                return
            elif key == ord('>'):
                if not self.game.explored[self.game.stairs_y][self.game.stairs_x]:
                    self.game.messages.append("You don't know where the downstairs are.")
                else:
                    self.game.walk_to_stairs('down')
                self.game.walk_mode = False
                return
            else:
                self.game.walk_mode = False

        if key == ord('w'):
            if not (self.game.explored[self.game.stairs_y][self.game.stairs_x] or
                    self.game.explored[self.game.stairs_up_y][self.game.stairs_up_x]):
                self.game.messages.append("You haven't found any stairs yet.")
            else:
                self.game.walk_mode = True
                self.game.messages.append("Walk to stairs: < or >")
            return

        movement_keys = {
            ord('8'): (0, -1), ord('k'): (0, -1), curses.KEY_UP: (0, -1),
            ord('2'): (0, 1), ord('j'): (0, 1), curses.KEY_DOWN: (0, 1),
            ord('4'): (-1, 0), ord('h'): (-1, 0), curses.KEY_LEFT: (-1, 0),
            ord('6'): (1, 0), ord('l'): (1, 0), curses.KEY_RIGHT: (1, 0),
            ord('7'): (-1, -1), ord('y'): (-1, -1), curses.KEY_HOME: (-1, -1), curses.KEY_A1: (-1, -1),
            ord('9'): (1, -1), ord('u'): (1, -1), curses.KEY_PPAGE: (1, -1), curses.KEY_A3: (1, -1),
            ord('1'): (-1, 1), ord('b'): (-1, 1), curses.KEY_END: (-1, 1), curses.KEY_C1: (-1, 1),
            ord('3'): (1, 1), ord('n'): (1, 1), curses.KEY_NPAGE: (1, 1), curses.KEY_C3: (1, 1),
        }

        if key in movement_keys:
            dx, dy = movement_keys[key]
            self.game.player_move_or_attack(dx, dy)
            return

        if key in [ord('5'), curses.KEY_B2]:
            # Passing a turn (numpad 5 or keypad center)
            self.game.process_turn()
            return

        if key == ord('i'):
            self.game.open_inventory()
        elif key == ord('c'):
            self.game.open_character_screen()
        elif key == ord(','):
            self.game.pickup_item()
        elif key == ord('>'):
            self.game.use_stairs('down')
        elif key == ord('<'):
            self.game.use_stairs('up')
        else:
            return  # Invalid key, don't process the turn

        self.game.process_turn()

    def handle_quit(self):
        self.game.messages.append("Are you sure you want to quit? Your character will be lost! (Y/N)")
        self.game.renderer.draw(self.game.stdscr)  # Use the renderer to draw
        while True:
            key = self.game.stdscr.getch()
            if key in [ord('Y'), ord('y')]:
                return True  # Signal to quit the game
            elif key in [ord('N'), ord('n'), 27]:  # 'N', 'n', or ESC
                self.game.messages.pop()  # Remove the confirmation message
                return False  # Don't quit, continue the game

    def handle_inventory_input(self, key):
        """Handle key presses while the inventory screen is open.

        Pressing the letter of an item will attempt to equip it. Page
        navigation is handled with '+' and '-'.  Press ESC to leave the
        inventory."""

        inventory_items = self.game.player.get_inventory_items()
        max_pages = (len(inventory_items) - 1) // self.game.items_per_page

        if key == 27:  # ESC key
            self.game.inventory_mode = False
            return

        if key in [ord('+'), ord('='), curses.KEY_NPAGE]:
            self.game.inventory_page = min(self.game.inventory_page + 1, max_pages)
        elif key in [ord('-'), curses.KEY_PPAGE]:
            self.game.inventory_page = max(0, self.game.inventory_page - 1)
        elif 97 <= key <= 122:  # a-z
            index = key - ord('a') + self.game.inventory_page * self.game.items_per_page
            if 0 <= index < len(inventory_items):
                item, _ = inventory_items[index]
                if isinstance(item, Equipment):
                    self.game.equip_item(item)
                else:
                    self.game.messages.append(f"{item.name} cannot be equipped.")
            else:
                self.game.messages.append("Invalid item.")

    def handle_character_screen_input(self, key):
        if key == 27:  # ESC key
            self.game.character_screen_mode = False

    def handle_equipment_input(self, key):
        if key == 27:  # ESC key
            self.game.equipment_mode = False
            self.game.equipment_slot = None
            return

        if self.game.equipment_slot is None:
            if 97 <= key <= 109:  # 'a' to 'm'
                self.game.equipment_slot = chr(key)
        else:
            if key in [ord('+'), ord('=')]:
                self.game.equipment_page += 1
            elif key == ord('-'):
                self.game.equipment_page = max(0, self.game.equipment_page - 1)
            elif 97 <= key <= 122:  # 'a' to 'z'
                self.game.equip_item(chr(key))
            self.game.equipment_slot = None

    def handle_character_stats_input(self, key):
        if key == 27:  # ESC key
            self.game.character_stats_mode = False

    def handle_backpack_input(self, key):
        if key == 27:  # ESC key
            self.game.backpack_mode = False
        elif key in [ord('+'), ord('=')]:
            self.game.backpack_page += 1
        elif key == ord('-'):
            self.game.backpack_page = max(0, self.game.backpack_page - 1)
        elif 97 <= key <= 122:  # a-z
            self.game.use_backpack_item(chr(key))

    def handle_debug_input(self, key):
        if key == 27:  # ESC key
            self.game.debug_mode = False
            return

        item = self.game.create_random_item()
        self.game.player.add_item(item)
        self.game.messages.append(f"Spawned {item.name} in your inventory.")
