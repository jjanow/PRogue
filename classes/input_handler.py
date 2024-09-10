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
        movement_keys = {
            ord('8'): (0, -1), ord('k'): (0, -1), curses.KEY_UP: (0, -1),
            ord('2'): (0, 1), ord('j'): (0, 1), curses.KEY_DOWN: (0, 1),
            ord('4'): (-1, 0), ord('h'): (-1, 0), curses.KEY_LEFT: (-1, 0),
            ord('6'): (1, 0), ord('l'): (1, 0), curses.KEY_RIGHT: (1, 0),
            ord('7'): (-1, -1), ord('y'): (-1, -1),
            ord('9'): (1, -1), ord('u'): (1, -1),
            ord('1'): (-1, 1), ord('b'): (-1, 1),
            ord('3'): (1, 1), ord('n'): (1, 1),
        }

        if key in movement_keys:
            dx, dy = movement_keys[key]
            self.game.player_move_or_attack(dx, dy)
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
        if key == 27:  # ESC key
            if self.game.selected_slot is not None:
                self.game.selected_slot = None
            else:
                self.game.inventory_mode = False
            return

        if self.game.selected_slot is None:
            if key in range(ord('a'), ord('m') + 1):
                self.game.selected_slot = chr(key)
            elif key in [ord('+'), ord('='), curses.KEY_NPAGE]:
                self.game.next_inventory_page()
            elif key in [ord('-'), curses.KEY_PPAGE]:
                self.game.prev_inventory_page()
            elif key == ord('E'):
                self.game.messages.append("Select an item to equip (a-z):")
            elif key == ord('U'):
                self.game.messages.append("Select a slot to unequip (a-m):")
            elif 97 <= key <= 109:  # a-m
                self.game.unequip_item(chr(key))
        else:
            equippable_items = [item for item in self.game.player.inventory if isinstance(item, Equipment) and item.slot == self.game.player.equipment[self.game.selected_slot]['name']]
            if key == ord('-') and not equippable_items:
                self.game.unequip_item(self.game.selected_slot)
            else:
                index = key - ord('a')
                if 0 <= index < len(equippable_items):
                    self.game.equip_item(equippable_items[index])
                self.game.selected_slot = None

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
