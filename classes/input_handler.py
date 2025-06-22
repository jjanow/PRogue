import curses

from classes.item import Equipment

class InputHandler:
    def __init__(self, game):
        self.game = game

    def handle_input(self, key):
        if self.game.debug_mode:
            self.handle_debug_input(key)
            return False  # Don't exit the game

        if self.game.help_mode:
            self.handle_help_input(key)
            return False

        if self.game.options_mode:
            self.handle_options_input(key)
            return False

        if self.game.save_load_menu_mode:
            self.handle_save_load_menu_input(key)
            return False

        if self.game.save_mode:
            self.handle_save_input(key)
            return False

        if self.game.load_mode:
            self.handle_load_input(key)
            return False

        if self.game.delete_mode:
            self.handle_delete_input(key)
            return False

        if self.game.inventory_mode:
            self.handle_inventory_input(key)
        elif self.game.backpack_mode:
            self.handle_backpack_input(key)
        elif self.game.character_screen_mode:
            self.handle_character_screen_input(key)
        elif self.game.character_stats_mode:
            self.handle_character_stats_input(key)
        elif self.game.combat_stats_mode:
            self.handle_combat_stats_input(key)
        elif key == ord('i'):
            self.game.inventory_mode = True
            self.game.inventory_page = 0
        elif key == ord('@'):
            self.game.open_character_stats_screen()
        elif key == ord('Q'):
            return self.handle_quit()
        elif key == ord('!'):  # Debug menu toggle
            self.game.debug_mode = True
        elif key == 27:  # ESC key
            self.game.save_load_menu_mode = True
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

        if key == 23:  # CTRL+W
            self.game.open_combat_stats_screen()
            return

        if key == ord('w'):
            if not (self.game.explored[self.game.stairs_y][self.game.stairs_x] or
                    self.game.explored[self.game.stairs_up_y][self.game.stairs_up_x]):
                self.game.messages.append("You haven't found any stairs yet.")
            else:
                self.game.walk_mode = True
                self.game.messages.append("Walk to stairs: < or >")
            return

        if key == ord('0'):
            self.game.auto_explore()
            return

        if key == ord('='):
            self.game.options_mode = True
            return
        if key == ord('?'):
            self.game.help_mode = True
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

        Pressing the letter of an item will equip it if possible or use it
        otherwise. Page navigation is handled with '+' and '-'.  Press ESC
        to leave the inventory."""

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
                    self.game.use_item(item)
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

    def handle_combat_stats_input(self, key):
        if key == 27:  # ESC key
            self.game.combat_stats_mode = False

    def handle_backpack_input(self, key):
        if key == 27:  # ESC key
            self.game.backpack_mode = False
        elif key in [ord('+'), ord('=')]:
            self.game.backpack_page += 1
        elif key == ord('-'):
            self.game.backpack_page = max(0, self.game.backpack_page - 1)
        elif 97 <= key <= 122:  # a-z
            self.game.use_backpack_item(chr(key))

    def handle_options_input(self, key):
        if key == 27:  # ESC key
            self.game.options_mode = False
            self.game.speed_input = ""
            return

        if key == 10:  # Enter key
            if self.game.speed_input:
                try:
                    new_speed = int(self.game.speed_input)
                    if 0 <= new_speed <= 1000:
                        self.game.walk_speed = new_speed
                        self.game.messages.append(f"Walking speed set to {new_speed} ms.")
                    else:
                        self.game.messages.append("Speed must be between 0 and 1000 ms.")
                except ValueError:
                    self.game.messages.append("Invalid speed value.")
                self.game.speed_input = ""
            return

        # Handle speed input
        if 48 <= key <= 57:  # 0-9
            self.game.speed_input += chr(key)
        elif key == 8 or key == 127:  # Backspace
            self.game.speed_input = self.game.speed_input[:-1]

    def handle_help_input(self, key):
        if key in (27, ord('q')):
            self.game.help_mode = False

    def handle_debug_input(self, key):
        # Handle debug menu options
        if key == 27:  # ESC key
            self.game.debug_mode = False
        elif key == ord('a'):  # Create weapon
            item = self.game.create_specific_item('weapon')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('b'):  # Create missile weapon
            item = self.game.create_specific_item('missile_weapon')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('c'):  # Create helmet
            item = self.game.create_specific_item('helmet')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('d'):  # Create amulet
            item = self.game.create_specific_item('amulet')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('e'):  # Create shield
            item = self.game.create_specific_item('shield')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('f'):  # Create armor
            item = self.game.create_specific_item('armor')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('g'):  # Create cloak
            item = self.game.create_specific_item('cloak')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('h'):  # Create girdle
            item = self.game.create_specific_item('girdle')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('i'):  # Create gauntlets
            item = self.game.create_specific_item('gauntlets')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('j'):  # Create boots
            item = self.game.create_specific_item('boots')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('k'):  # Create ring
            item = self.game.create_specific_item('ring')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('l'):  # Create bracers
            item = self.game.create_specific_item('bracers')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('m'):  # Create potion
            item = self.game.create_specific_item('potion')
            if item:
                self.game.player.add_item(item)
                self.game.messages.append(f"Created {item.name} in your inventory.")
        elif key == ord('n'):  # Map level
            self.game.map_current_level()
        elif key == ord('o'):  # Level up
            self.game.level_up_player()
        elif key == ord('s'):  # Spawn random item (legacy)
            self.game.spawn_item_in_inventory()
        elif key == ord('t'):  # Add time
            self.game.time += 1000
            self.game.messages.append("Added 1000 time units.")
        elif key == ord('w'):  # Decrease walk speed
            self.game.walk_speed = max(1, self.game.walk_speed - 1)
            self.game.messages.append(f"Walk speed decreased to {self.game.walk_speed} ms.")
        elif key == ord('e'):  # Increase walk speed
            self.game.walk_speed = min(100, self.game.walk_speed + 1)
            self.game.messages.append(f"Walk speed increased to {self.game.walk_speed} ms.")

    def handle_save_input(self, key):
        """Handle input for save game mode."""
        if key == 27:  # ESC key
            self.game.save_mode = False
            self.game.save_slot = None
            return
        
        if self.game.save_slot is None:
            if 49 <= key <= 57:  # '1' to '9'
                self.game.save_slot = key - ord('0')
            elif key == ord('0'):  # '0' for slot 10
                self.game.save_slot = 10
        else:
            if key == ord('y') or key == ord('Y'):
                try:
                    self.game.save_manager.save_game(self.game, self.game.save_slot)
                    self.game.messages.append(f"Game saved to slot {self.game.save_slot}.")
                except Exception as e:
                    self.game.messages.append(f"Failed to save game: {e}")
                self.game.save_mode = False
                self.game.save_slot = None
            elif key == ord('n') or key == ord('N') or key == 27:
                self.game.save_mode = False
                self.game.save_slot = None

    def handle_load_input(self, key):
        """Handle input for load game mode."""
        if key == 27:  # ESC key
            self.game.load_mode = False
            self.game.save_slot = None
            return
        
        if self.game.save_slot is None:
            if 49 <= key <= 57:  # '1' to '9'
                self.game.save_slot = key - ord('0')
            elif key == ord('0'):  # '0' for slot 10
                self.game.save_slot = 10
        else:
            if key == ord('y') or key == ord('Y'):
                try:
                    self.game.save_manager.load_game(self.game, self.game.save_slot)
                    self.game.messages.append(f"Game loaded from slot {self.game.save_slot}.")
                except Exception as e:
                    self.game.messages.append(f"Failed to load game: {e}")
                self.game.load_mode = False
                self.game.save_slot = None
            elif key == ord('n') or key == ord('N') or key == 27:
                self.game.load_mode = False
                self.game.save_slot = None

    def handle_delete_input(self, key):
        """Handle input for delete save mode."""
        if key == 27:  # ESC key
            self.game.delete_mode = False
            self.game.save_slot = None
            return
        
        if self.game.save_slot is None:
            if 49 <= key <= 57:  # '1' to '9'
                self.game.save_slot = key - ord('0')
            elif key == ord('0'):  # '0' for slot 10
                self.game.save_slot = 10
        else:
            if key == ord('y') or key == ord('Y'):
                try:
                    if self.game.save_manager.delete_save(self.game.save_slot):
                        self.game.messages.append(f"Save slot {self.game.save_slot} deleted.")
                    else:
                        self.game.messages.append(f"Save slot {self.game.save_slot} was already empty.")
                except Exception as e:
                    self.game.messages.append(f"Failed to delete save: {e}")
                self.game.delete_mode = False
                self.game.save_slot = None
            elif key == ord('n') or key == ord('N') or key == 27:
                self.game.delete_mode = False
                self.game.save_slot = None

    def handle_save_load_menu_input(self, key):
        """Handle input for the save/load menu accessed by pressing ESC."""
        if key == 27:  # ESC key
            self.game.save_load_menu_mode = False
            return
        
        if key == ord('s'):
            self.game.save_mode = True
            self.game.save_load_menu_mode = False
            return
        
        if key == ord('l'):
            self.game.load_mode = True
            self.game.save_load_menu_mode = False
            return
        
        if key == ord('d'):
            self.game.delete_mode = True
            self.game.save_load_menu_mode = False
            return
