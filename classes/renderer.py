from __future__ import annotations

import curses
from typing import TYPE_CHECKING

from classes.item import Equipment, Item
from classes.save_manager import SaveInfo

if TYPE_CHECKING:
    from classes.game import Game


ITEM_ICONS = {
    'weapon': '/',
    'missile weapon': '}',
    'helmet': '^',
    'armor': '[',
    'cloak': 'B',
    'shield': ')',
    'boots': '(',
    'bracers': '|',
    'gauntlets': ']',
    'girdle': ':',
    'amulet': '"',
    'ring (right)': '=',
    'ring (left)': '=',
}

class Renderer:
    def __init__(self, game: Game) -> None:
        self.game = game

    def _icon_for(self, item: Item) -> str:
        if isinstance(item, Equipment):
            return ITEM_ICONS.get(item.slot, '?')
        return '!'

    def _format_item_stats(self, item: Item) -> str:
        info: list[str] = []
        if isinstance(item, Equipment):
            equipped: Equipment | None = None
            for _slot_key, slot in self.game.player.equipment.items():
                if slot['name'] == item.slot:
                    equipped = slot['item']
                    break
            if item.damage is not None:
                dmg = (
                    f"{item.damage.get('min',0)}-{item.damage.get('max',0)}"
                    if isinstance(item.damage, dict)
                    else str(item.damage)
                )
                if equipped and equipped.damage is not None:
                    eqd = (
                        f"{equipped.damage.get('min',0)}-{equipped.damage.get('max',0)}"
                        if isinstance(equipped.damage, dict)
                        else str(equipped.damage)
                    )
                    info.append(f"DMG {eqd}->{dmg}")
                else:
                    info.append(f"DMG {dmg}")
            if item.ac:
                if equipped and equipped.ac:
                    info.append(f"AC {equipped.ac}->{item.ac}")
                else:
                    info.append(f"AC {item.ac}")
            if item.accuracy_bonus:
                if equipped and equipped.accuracy_bonus:
                    info.append(f"ACC {equipped.accuracy_bonus}->{item.accuracy_bonus}")
                else:
                    info.append(f"ACC {item.accuracy_bonus}")
            if item.stat_boost:
                if equipped and equipped.stat_boost:
                    info.append(f"STAT {equipped.stat_boost}->{item.stat_boost}")
                else:
                    info.append(f"STAT {item.stat_boost}")
            info.append(f"WT {item.weight}")
        else:
            if getattr(item, 'effect_type', None) == 'heal':
                info.append(f"Heal {item.value}")
            elif getattr(item, 'effect_type', None) == 'restore_mana':
                info.append(f"Mana {item.value}")
            else_effect: str = getattr(item, 'effect_type', '') or ''
            if else_effect.startswith('boost_'):
                stat = else_effect.split('_', 1)[1].title()
                info.append(f"+{item.value} {stat}")
            info.append(f"WT {item.weight}")
        return ' '.join(info)

    def draw(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Rows available for the map viewport (6 rows reserved for status + messages)
        vp_h = max(1, height - 6)
        vp_w = max(1, width)

        map_grid = self.game.map
        map_h = len(map_grid)
        map_w = len(map_grid[0]) if map_grid else 0

        # Camera: keep player centred, clamped to map bounds
        px, py = self.game.player.x, self.game.player.y
        cam_x = max(0, min(px - vp_w // 2, map_w - vp_w)) if map_w > vp_w else 0
        cam_y = max(0, min(py - vp_h // 2, map_h - vp_h)) if map_h > vp_h else 0

        # Centre the map in the viewport when it is smaller than the terminal
        off_x = (vp_w - map_w) // 2 if map_w < vp_w else 0
        off_y = (vp_h - map_h) // 2 if map_h < vp_h else 0

        for sy in range(min(vp_h, map_h)):
            my = sy + cam_y
            for sx in range(min(vp_w, map_w)):
                mx = sx + cam_x
                if not self.game.explored[my][mx]:
                    stdscr.addch(sy + off_y, sx + off_x, ' ')
                    continue

                visible = self.game.visible[my][mx]
                attr = curses.A_NORMAL if visible else curses.A_DIM
                cell = map_grid[my][mx]

                if cell == '#':
                    stdscr.addch(sy + off_y, sx + off_x, cell, curses.color_pair(5) | attr)
                elif cell in ('+',):
                    stdscr.addch(sy + off_y, sx + off_x, cell, curses.color_pair(6) | attr)
                elif cell == '/':
                    stdscr.addch(sy + off_y, sx + off_x, cell, curses.color_pair(6) | attr)
                elif cell == 'T':
                    stdscr.addch(sy + off_y, sx + off_x, cell, curses.color_pair(8) | attr)
                elif cell == '~':
                    stdscr.addch(sy + off_y, sx + off_x, cell, curses.color_pair(9) | attr)
                else:
                    stdscr.addch(sy + off_y, sx + off_x, cell, curses.color_pair(1) | attr)

        for item in self.game.items:
            iy, ix = item.y, item.x
            if iy is None or ix is None:
                continue
            sy, sx = iy - cam_y, ix - cam_x
            if not (0 <= sy < vp_h and 0 <= sx < vp_w):
                continue
            if not (
                self.game.visible[iy][ix]
                or (item.seen and self.game.explored[iy][ix])
            ):
                continue
            icon = self._icon_for(item)
            attr = curses.A_NORMAL if self.game.visible[iy][ix] else curses.A_DIM
            stdscr.addch(sy + off_y, sx + off_x, icon, curses.color_pair(4) | attr)

        for enemy in self.game.enemies:
            sy, sx = enemy.y - cam_y, enemy.x - cam_x
            if (
                0 <= sy < vp_h
                and 0 <= sx < vp_w
                and self.game.visible[enemy.y][enemy.x]
            ):
                attr = curses.color_pair(3)
                if enemy.ai_state.state == "asleep":
                    attr |= curses.A_REVERSE
                stdscr.addch(sy + off_y, sx + off_x, enemy.char, attr)

        py_s, px_s = self.game.player.y - cam_y, self.game.player.x - cam_x
        if 0 <= py_s < vp_h and 0 <= px_s < vp_w:
            stdscr.addch(py_s + off_y, px_s + off_x, self.game.player.char, curses.color_pair(2))

        # Status bar
        stdscr.addstr(
            height - 6,
            0,
            f"Health: {self.game.player.health}/{self.game.player.max_health} | Damage: {self.game.player.damage:.1f} | Defense: {self.game.player.defense:.1f}",
        )
        location = "Millhaven (Town)" if self.game.in_town else f"Dungeon Level {self.game.dungeon_level}"
        stdscr.addstr(height - 5, 0, f"Level: {self.game.player.level} | XP: {self.game.player.xp}/{self.game.player.xp_to_next_level} | Location: {location}")

        if self.game.rest_mode:
            stdscr.addstr(height - 4, 0, "Resting..."[:width - 1], curses.color_pair(6))

        for i, message in enumerate(self.game.messages[-3:]):
            if height - 3 + i < height:
                stdscr.addstr(height - 3 + i, 0, str(message)[:width])

        stdscr.refresh()

    def draw_inventory(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        header = "Inventory (press escape to exit, '+' for next page, '-' for previous page)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        inventory_items = self.game.player.get_inventory_items()
        start_index = self.game.inventory_page * self.game.items_per_page
        end_index = start_index + self.game.items_per_page

        for i, (item, count) in enumerate(inventory_items[start_index:end_index], start=0):
            key = chr(97 + i)  # a-z
            info = self._format_item_stats(item)
            name_part = f"{key}) {item.name} [{count}] "
            stdscr.addstr(i + 2, 0, name_part[:width-1], curses.color_pair(4))
            start_col = len(name_part)
            if start_col < width - 1:
                stdscr.addstr(
                    i + 2,
                    start_col,
                    info[: width - 1 - start_col],
                    curses.color_pair(6),
                )

        total_pages = max(1, (len(inventory_items) - 1) // self.game.items_per_page + 1)
        footer = f"Page {self.game.inventory_page + 1}/{total_pages}"
        stdscr.addstr(height - 1, 0, footer[:width-1], curses.color_pair(7))

        stdscr.refresh()

    def draw_character_screen(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        header = "Character Information (press escape to exit)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        # Left column: Basic Info
        left_column: list[str] = [
            f"Name: {self.game.player.name.title()}",
            f"Level: {self.game.player.level}",
            f"XP: {self.game.player.xp}/{self.game.player.xp_to_next_level}",
            "",
            f"Health: {self.game.player.health}/{self.game.player.max_health}",
            f"Mana: {self.game.player.mana}/{self.game.player.max_mana}",
            f"Psi: {self.game.player.psi}/{self.game.player.max_psi}",
            "",
            f"Base Damage: {self.game.player.base_damage}",
            f"Base Defense: {self.game.player.base_defense}",
            f"Total Damage: {self.game.player.damage:.1f}",
            f"Total Defense: {self.game.player.defense:.1f}",
            "",
            f"Money: {self.game.player.money} gold",
        ]

        # Right column: ADOM-style stats
        right_column: list[str] = [
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

    def draw_backpack(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        header = "Backpack Items (press '+' for next page, '-' for previous page, escape to exit)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        backpack_items = self.game.player.get_inventory_items()
        items_per_page = self.game.items_per_page
        start_index = self.game.backpack_page * items_per_page
        end_index = start_index + items_per_page

        for i, (item, count) in enumerate(backpack_items[start_index:end_index], start=0):
            key = chr(97 + i)  # a-z
            item_str = f"{key}) {item.name} [{count}]"
            stdscr.addstr(i + 2, 0, item_str[:width-1], curses.color_pair(4))

        total_pages = (len(backpack_items) - 1) // items_per_page + 1
        footer = f"Page {self.game.backpack_page + 1}/{total_pages}"
        stdscr.addstr(height - 1, 0, footer[:width-1], curses.color_pair(7))

        stdscr.refresh()

    def draw_drop_interface(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        header = "Drop Items (press '+' for next page, '-' for previous page, escape to exit)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        backpack_items = self.game.player.get_inventory_items()
        items_per_page = self.game.items_per_page
        start_index = self.game.backpack_page * items_per_page
        end_index = start_index + items_per_page

        for i, (item, count) in enumerate(backpack_items[start_index:end_index], start=0):
            key = chr(97 + i)  # a-z
            item_str = f"{key}) {item.name} [{count}]"
            stdscr.addstr(i + 2, 0, item_str[:width-1], curses.color_pair(4))

        total_pages = (len(backpack_items) - 1) // items_per_page + 1
        footer = f"Page {self.game.backpack_page + 1}/{total_pages}"
        stdscr.addstr(height - 1, 0, footer[:width-1], curses.color_pair(7))

        stdscr.refresh()


    def draw_equipment_screen(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, _width = stdscr.getmaxyx()

        stdscr.addstr(0, 0, "Equipment:", curses.color_pair(7))
        for i, (key, slot) in enumerate(self.game.player.equipment.items()):
            item = slot['item']
            item_name = item.name if item else "Empty"
            stdscr.addstr(i + 2, 0, f"{key}: {slot['name']}: {item_name}")

            # Display equippable items for each slot
            equippable_items: list[Equipment] = [item for item in self.game.player.inventory if isinstance(item, Equipment) and item.slot == slot['name']]
            if equippable_items:
                stdscr.addstr(i + 2, 40, f"Equippable: {', '.join(item.name for item in equippable_items)}")

        stdscr.addstr(height - 1, 0, "Press the letter of a slot to equip an item, or 'q' to exit", curses.color_pair(7))
        stdscr.refresh()

    def draw_character_stats_screen(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        header = "Character Stats (press escape to exit)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        # Attribute Scores
        attributes: list[str] = [
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
        misc_data: list[str] = [
            f"Name: {self.game.player.name.title()}",
            f"Gender: {getattr(self.game.player, 'gender', 'Unknown').title()}",
            f"Sex: {getattr(self.game.player, 'sex', 'Unknown')}",
            f"Race: {getattr(self.game.player, 'race', 'Unknown')}",
            f"HP: {self.game.player.health}/{self.game.player.max_health}",
            f"PP: {self.game.player.psi}/{self.game.player.max_psi}",
            f"Speed: {self.game.player.speed}",
            f"Money: {self.game.player.money} gold",
        ]

        # Equipment Data
        equipment_lines: list[str] = [
            f"{slot['name'].title()}: {slot['item'].name if slot['item'] else 'Empty'}"
            for slot in self.game.player.equipment.values()
        ]

        left_lines: list[str] = attributes + [""] + misc_data
        left_width = width // 2 - 2

        for i, line in enumerate(left_lines, start=2):
            if i >= height:
                break
            stdscr.addstr(i, 0, line[:left_width])

        right_start = 1
        stdscr.addstr(right_start, width // 2, "Equipment:", curses.color_pair(7))
        for i, line in enumerate(equipment_lines, start=right_start + 1):
            if i >= height:
                break
            stdscr.addstr(i, width // 2, line[:width // 2 - 1])

        stdscr.refresh()

    def draw_debug_menu(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        menu_text: list[str] = [
            "Debug Menu (press escape to exit):",
            "",
            "Item Creation:",
            "a) Create weapon",
            "b) Create missile weapon",
            "c) Create helmet",
            "d) Create amulet",
            "e) Create shield",
            "f) Create armor",
            "g) Create cloak",
            "h) Create girdle",
            "i) Create gauntlets",
            "j) Create boots",
            "k) Create ring",
            "l) Create bracers",
            "m) Create potion",
            "",
            "Game Functions:",
            "n) Map current level",
            "o) Level up player",
            "s) Spawn random item",
            "",
            "Debug Functions:",
            "t) Add 1000 time units",
            "w) Decrease walk speed",
            "p) Increase walk speed",
        ]

        for i, line in enumerate(menu_text):
            if i >= height - 1:  # Leave room for potential messages
                break
            if line == "":
                continue  # Skip empty lines if we're running out of space
            color = curses.color_pair(7) if i == 0 else curses.color_pair(4)
            stdscr.addstr(i, 0, line[:width-1], color)

        stdscr.refresh()

    def draw_options_menu(self, stdscr: curses.window) -> None:
        stdscr.clear()
        _height, width = stdscr.getmaxyx()

        lines: list[str] = [
            "Options (press escape to exit):",
            f"Walking speed: {self.game.walk_speed} ms (enter 0-1000)",
            "",
            "Press ESC for save/load operations",
        ]

        if self.game.speed_input:
            lines.append(f"New speed: {self.game.speed_input}")

        for i, line in enumerate(lines):
            color = curses.color_pair(7) if i == 0 else curses.color_pair(4)
            stdscr.addstr(i, 0, line[:width-1], color)

        stdscr.refresh()

    def draw_save_screen(self, stdscr: curses.window) -> None:
        """Draw the save game screen."""
        stdscr.clear()
        _height, width = stdscr.getmaxyx()

        header = "Save Game (press escape to exit)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        if self.game.save_slot is None:
            saves: list[SaveInfo] = self.game.save_info_cache or self.game.save_manager.get_all_save_info()
            stdscr.addstr(2, 0, "Select a save slot (1-0):", curses.color_pair(4))

            for i, save in enumerate(saves, 1):
                exists = save['exists']
                assert isinstance(exists, bool)
                if exists:
                    timestamp = save['timestamp']
                    assert isinstance(timestamp, str)
                    timestamp = timestamp[:19] if timestamp != 'Unknown' else 'Unknown'
                    character_name = save['character_name']
                    player_level = save['player_level']
                    level = save['level']
                    line = f"{i}) {character_name} - Level {player_level} (Dungeon {level}) - {timestamp}"
                else:
                    line = f"{i}) Empty slot"

                color = curses.color_pair(4)
                if i == 10:
                    stdscr.addstr(i + 2, 0, f"0) {line[3:]}", color)
                else:
                    stdscr.addstr(i + 2, 0, line, color)
        else:
            # Confirm save
            save_info = self.game.save_manager.get_save_info(self.game.save_slot)
            exists = save_info['exists']
            assert isinstance(exists, bool)
            if exists:
                stdscr.addstr(2, 0, f"Overwrite save slot {self.game.save_slot}?", curses.color_pair(4))
                stdscr.addstr(3, 0, f"Character: {save_info['character_name']}", curses.color_pair(4))
                stdscr.addstr(4, 0, f"Level: {save_info['player_level']} (Dungeon {save_info['level']})", curses.color_pair(4))
            else:
                stdscr.addstr(2, 0, f"Save to slot {self.game.save_slot}?", curses.color_pair(4))

            stdscr.addstr(6, 0, "Press Y to confirm, N to cancel", curses.color_pair(4))

        stdscr.refresh()

    def draw_load_screen(self, stdscr: curses.window) -> None:
        """Draw the load game screen."""
        stdscr.clear()
        _height, width = stdscr.getmaxyx()

        header = "Load Game (press escape to exit)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        if self.game.save_slot is None:
            saves: list[SaveInfo] = self.game.save_info_cache or self.game.save_manager.get_all_save_info()
            stdscr.addstr(2, 0, "Select a save slot to load (1-0):", curses.color_pair(4))

            for i, save in enumerate(saves, 1):
                exists = save['exists']
                assert isinstance(exists, bool)
                if exists:
                    timestamp = save['timestamp']
                    assert isinstance(timestamp, str)
                    timestamp = timestamp[:19] if timestamp != 'Unknown' else 'Unknown'
                    character_name = save['character_name']
                    player_level = save['player_level']
                    level = save['level']
                    line = f"{i}) {character_name} - Level {player_level} (Dungeon {level}) - {timestamp}"
                    color = curses.color_pair(4)
                else:
                    line = f"{i}) Empty slot"
                    color = curses.color_pair(6)

                if i == 10:
                    stdscr.addstr(i + 2, 0, f"0) {line[3:]}", color)
                else:
                    stdscr.addstr(i + 2, 0, line, color)
        else:
            # Confirm load
            save_info = self.game.save_manager.get_save_info(self.game.save_slot)
            exists = save_info['exists']
            assert isinstance(exists, bool)
            if exists:
                stdscr.addstr(2, 0, f"Load save slot {self.game.save_slot}?", curses.color_pair(4))
                stdscr.addstr(3, 0, f"Character: {save_info['character_name']}", curses.color_pair(4))
                stdscr.addstr(4, 0, f"Level: {save_info['player_level']} (Dungeon {save_info['level']})", curses.color_pair(4))
                stdscr.addstr(6, 0, "Press Y to confirm, N to cancel", curses.color_pair(4))
            else:
                stdscr.addstr(2, 0, f"Save slot {self.game.save_slot} is empty!", curses.color_pair(3))
                stdscr.addstr(4, 0, "Press any key to continue", curses.color_pair(4))

        stdscr.refresh()

    def draw_delete_screen(self, stdscr: curses.window) -> None:
        """Draw the delete save screen."""
        stdscr.clear()
        _height, width = stdscr.getmaxyx()

        header = "Delete Save (press escape to exit)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        if self.game.save_slot is None:
            saves: list[SaveInfo] = self.game.save_info_cache or self.game.save_manager.get_all_save_info()
            stdscr.addstr(2, 0, "Select a save slot to delete (1-0):", curses.color_pair(4))

            for i, save in enumerate(saves, 1):
                exists = save['exists']
                assert isinstance(exists, bool)
                if exists:
                    timestamp = save['timestamp']
                    assert isinstance(timestamp, str)
                    timestamp = timestamp[:19] if timestamp != 'Unknown' else 'Unknown'
                    character_name = save['character_name']
                    player_level = save['player_level']
                    level = save['level']
                    line = f"{i}) {character_name} - Level {player_level} (Dungeon {level}) - {timestamp}"
                    color = curses.color_pair(4)
                else:
                    line = f"{i}) Empty slot"
                    color = curses.color_pair(6)

                if i == 10:
                    stdscr.addstr(i + 2, 0, f"0) {line[3:]}", color)
                else:
                    stdscr.addstr(i + 2, 0, line, color)
        else:
            # Confirm delete
            save_info = self.game.save_manager.get_save_info(self.game.save_slot)
            exists = save_info['exists']
            assert isinstance(exists, bool)
            if exists:
                stdscr.addstr(2, 0, f"Delete save slot {self.game.save_slot}?", curses.color_pair(3))
                stdscr.addstr(3, 0, f"Character: {save_info['character_name']}", curses.color_pair(4))
                stdscr.addstr(4, 0, f"Level: {save_info['player_level']} (Dungeon {save_info['level']})", curses.color_pair(4))
                stdscr.addstr(6, 0, "Press Y to confirm, N to cancel", curses.color_pair(4))
            else:
                stdscr.addstr(2, 0, f"Save slot {self.game.save_slot} is already empty!", curses.color_pair(3))
                stdscr.addstr(4, 0, "Press any key to continue", curses.color_pair(4))

        stdscr.refresh()

    def draw_save_load_menu(self, stdscr: curses.window) -> None:
        """Draw the save/load menu accessed by pressing ESC."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        header = "Save/Load Menu (press escape to exit)"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(7))

        lines: list[str] = [
            "",
            "s) Save game",
            "l) Load game",
            "d) Delete save",
            "",
            "Press the letter of your choice or ESC to exit."
        ]

        for i, line in enumerate(lines):
            if i >= height:
                break
            color = curses.color_pair(7) if i == 0 else curses.color_pair(4)
            stdscr.addstr(i, 0, line[:width-1], color)

        stdscr.refresh()

    def draw_help_menu(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        lines: list[str] = [
            "Help (press escape to exit):",
            "Movement: hjkl or arrow keys; diagonals yubn",
            "Wait: 5",
            "Pick up item: ','",
            "Open door: o (or walk into it)",
            "Close door: c",
            "Open inventory: i",
            "Character info: @",
            "Auto-explore: 0",
            "Rest until healed: r",
            "Walk to stairs: w",
            "Combat stats: Ctrl+W",
            "Options menu: =",
            "Save/Load menu: ESC",
            "Quit game: Q",
            "Show this help: ?",
        ]

        for i, line in enumerate(lines):
            if i >= height:
                break
            color = curses.color_pair(7) if i == 0 else curses.color_pair(4)
            stdscr.addstr(i, 0, line[:width-1], color)

        stdscr.refresh()

    def draw_combat_stats_screen(self, stdscr: curses.window) -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        dmg_lines: list[str] = ["Combat Stats (press escape to exit):", "", "Damage Breakdown:"]
        for src, val in self.game.player.damage_breakdown():
            dmg_lines.append(f"  {src}: {val:.1f}")
        dmg_lines.append(f"  Total Damage: {self.game.player.damage:.1f}")

        def_lines: list[str] = ["", "Defense Breakdown:"]
        for src, val in self.game.player.defense_breakdown():
            def_lines.append(f"  {src}: {val:.1f}")
        def_lines.append(f"  Total Defense: {self.game.player.defense:.1f}")

        lines: list[str] = dmg_lines + def_lines

        for i, line in enumerate(lines):
            if i >= height:
                break
            color = curses.color_pair(7) if i == 0 else curses.color_pair(4)
            stdscr.addstr(i, 0, line[:width-1], color)

        stdscr.refresh()
