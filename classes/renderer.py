import curses

from classes.item import Equipment

class Renderer:
    def __init__(self, game):
        self.game = game

    def draw(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Adjust the height to reserve 3 lines for the message log and 3 lines for the status bar
        dungeon_height = height - 6
        
        for y, row in enumerate(self.game.map[:dungeon_height]):
            for x, cell in enumerate(row[:width]):  # Ensure we don't exceed the screen width
                if cell == '#':
                    stdscr.addch(y, x, cell, curses.color_pair(5))  # Walls
                elif cell == '+':
                    stdscr.addch(y, x, cell, curses.color_pair(6))  # Doors
                else:
                    stdscr.addch(y, x, cell, curses.color_pair(1))  # Default

        for item in self.game.items:
            if item.y < dungeon_height:
                stdscr.addch(item.y, item.x, item.char, curses.color_pair(4))  # Items

        for enemy in self.game.enemies:
            if enemy.y < dungeon_height:
                stdscr.addch(enemy.y, enemy.x, enemy.char, curses.color_pair(3))  # Monsters

        if self.game.player.y < dungeon_height:
            stdscr.addch(self.game.player.y, self.game.player.x, self.game.player.char, curses.color_pair(2))  # Player

        # Status bar
        stdscr.addstr(height - 6, 0, f"Health: {self.game.player.health}/{self.game.player.max_health} | Damage: {self.game.player.damage} | Defense: {self.game.player.defense}")
        stdscr.addstr(height - 5, 0, f"Level: {self.game.player.level} | XP: {self.game.player.xp}/{self.game.player.xp_to_next_level} | Dungeon Level: {self.game.dungeon_level}")

        # Messages
        for i, message in enumerate(self.game.messages[-3:]):
            if message is not None and height - 3 + i < height:  # Ensure we don't write outside the window height
                stdscr.addstr(height - 3 + i, 0, str(message)[:width])  # Convert to string and truncate if too long

        stdscr.refresh()

    def draw_inventory(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        header = "Inventory (press escape to exit, '+' for next page, '-' for previous page)"
        stdscr.addstr(0, 0, header[:width-1])

        inventory_items = self.game.player.get_inventory_items()
        start_index = self.game.inventory_page * self.game.items_per_page
        end_index = start_index + self.game.items_per_page

        for i, (item, count) in enumerate(inventory_items[start_index:end_index], start=0):
            key = chr(97 + i)  # a-z
            item_str = f"{key}) {item.name} [{count}]"
            stdscr.addstr(i + 2, 0, item_str[:width-1])

        total_pages = max(1, (len(inventory_items) - 1) // self.game.items_per_page + 1)
        footer = f"Page {self.game.inventory_page + 1}/{total_pages}"
        stdscr.addstr(height - 1, 0, footer[:width-1])

        stdscr.refresh()

    def draw_character_screen(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        header = "Character Information (press escape to exit)"
        stdscr.addstr(0, 0, header[:width-1])

        # Left column: Basic Info
        left_column = [
            f"Name: {self.game.player.name}",
            f"Level: {self.game.player.level}",
            f"XP: {self.game.player.xp}/{self.game.player.xp_to_next_level}",
            "",
            f"Health: {self.game.player.health}/{self.game.player.max_health}",
            f"Mana: {self.game.player.mana}/{self.game.player.max_mana}",
            f"Psi: {self.game.player.psi}/{self.game.player.max_psi}",
            "",
            f"Base Damage: {self.game.player.base_damage}",
            f"Base Defense: {self.game.player.base_defense}",
            f"Total Damage: {self.game.player.damage}",
            f"Total Defense: {self.game.player.defense}",
            "",
            f"Money: {self.game.player.money} gold",
        ]

        # Right column: ADOM-style stats
        right_column = [
            f"Strength: {self.game.player.strength}",
            f"Dexterity: {self.game.player.dexterity}",
            f"Constitution: {self.game.player.constitution}",
            f"Intelligence: {self.game.player.intelligence}",
            f"Willpower: {self.game.player.willpower}",
            f"Charisma: {self.game.player.charisma}",
            "",
            f"Appearance: {self.game.player.appearance}",
            f"Perception: {self.game.player.perception}",
            "",
            f"Speed: {self.game.player.speed}",
        ]

        # Calculate column widths
        left_width = max(len(line) for line in left_column)
        right_width = max(len(line) for line in right_column)
        total_width = left_width + right_width + 4  # 4 for padding

        # Adjust if total width is greater than screen width
        if total_width > width:
            excess = total_width - width
            left_width = max(20, left_width - excess // 2)
            right_width = max(20, right_width - excess // 2)

        # Draw left column
        for i, line in enumerate(left_column, start=2):
            if i >= height:
                break
            stdscr.addstr(i, 0, line[:left_width])

        # Draw right column
        for i, line in enumerate(right_column, start=2):
            if i >= height:
                break
            stdscr.addstr(i, left_width + 2, line[:right_width])

        stdscr.refresh()

    def draw_backpack(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        header = "Backpack Items (press '+' for next page, '-' for previous page, escape to exit)"
        stdscr.addstr(0, 0, header[:width-1])

        backpack_items = self.game.player.get_inventory_items()
        items_per_page = self.game.items_per_page
        start_index = self.game.backpack_page * items_per_page
        end_index = start_index + items_per_page

        for i, (item, count) in enumerate(backpack_items[start_index:end_index], start=0):
            key = chr(97 + i)  # a-z
            item_str = f"{key}) {item.name} [{count}]"
            stdscr.addstr(i + 2, 0, item_str[:width-1])

        total_pages = (len(backpack_items) - 1) // items_per_page + 1
        footer = f"Page {self.game.backpack_page + 1}/{total_pages}"
        stdscr.addstr(height - 1, 0, footer[:width-1])

        stdscr.refresh()

    def draw_drop_interface(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        header = "Drop Items (press '+' for next page, '-' for previous page, escape to exit)"
        stdscr.addstr(0, 0, header[:width-1])

        backpack_items = self.game.player.get_inventory_items()
        items_per_page = self.game.items_per_page
        start_index = self.game.backpack_page * items_per_page
        end_index = start_index + items_per_page

        for i, (item, count) in enumerate(backpack_items[start_index:end_index], start=0):
            key = chr(97 + i)  # a-z
            item_str = f"{key}) {item.name} [{count}]"
            stdscr.addstr(i + 2, 0, item_str[:width-1])

        total_pages = (len(backpack_items) - 1) // items_per_page + 1
        footer = f"Page {self.game.backpack_page + 1}/{total_pages}"
        stdscr.addstr(height - 1, 0, footer[:width-1])

        stdscr.refresh()

    def draw_equipment_screen(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(0, 0, "Equipment:")
        for i, (key, slot) in enumerate(self.game.player.equipment.items()):
            item = slot['item']
            item_name = item.name if item else "Empty"
            stdscr.addstr(i + 2, 0, f"{key}: {slot['name']}: {item_name}")

            # Display equippable items for each slot
            equippable_items = [item for item in self.game.player.inventory if isinstance(item, Equipment) and item.slot == slot['name']]
            if equippable_items:
                stdscr.addstr(i + 2, 40, f"Equippable: {', '.join(item.name for item in equippable_items)}")

        stdscr.addstr(height - 1, 0, "Press the letter of a slot to equip an item, or 'q' to exit")
        stdscr.refresh()

    def draw_character_stats_screen(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        header = "Character Stats (press escape to exit)"
        stdscr.addstr(0, 0, header[:width-1])

        # Attribute Scores
        attributes = [
            f"Strength: {self.game.player.strength}",
            f"Learning: {self.game.player.intelligence}",
            f"Willpower: {self.game.player.willpower}",
            f"Dexterity: {self.game.player.dexterity}",
            f"Toughness: {self.game.player.constitution}",
            f"Charisma: {self.game.player.charisma}",
            f"Appearance: {self.game.player.appearance}",
            f"Mana: {self.game.player.mana}",
            f"Perception: {self.game.player.perception}",
        ]

        # Miscellaneous Data
        misc_data = [
            f"HP: {self.game.player.health}/{self.game.player.max_health}",
            f"PP: {self.game.player.psi}/{self.game.player.max_psi}",
            f"Speed: {self.game.player.speed}",
            f"Money: {self.game.player.money} gold",
            f"Deity: {self.game.player.deity}",
            f"Birth: {self.game.player.birth}",
            f"Month: {self.game.player.month}",
            f"Day: {self.game.player.day}",
            f"Age: {self.game.player.age} years",
        ]

        # Draw attributes
        for i, line in enumerate(attributes, start=2):
            if i >= height:
                break
            stdscr.addstr(i, 0, line[:width-1])

        # Draw miscellaneous data
        for i, line in enumerate(misc_data, start=2):
            if i >= height:
                break
            stdscr.addstr(i, width // 2, line[:width-1])

        stdscr.refresh()

    def draw_debug_menu(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        menu_text = [
            "Debug Menu (press escape to exit):",
            "i) Spawn an item",
            "x) Gain 100 XP",
            "m) Gain 100 gold"
        ]

        for i, line in enumerate(menu_text):
            stdscr.addstr(i, 0, line[:width-1])

        stdscr.refresh()
